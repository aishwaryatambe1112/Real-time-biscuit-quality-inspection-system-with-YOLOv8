"""
backend/routes/detection.py
============================
SocketIO + REST for camera & batch control.

KEY FIX: on_start_batch now passes `brand` to engine.start_batch(brand, cb).
The engine stores it as self._active_brand and ONLY that model runs.
"""

import os
import sys
import threading
from datetime import datetime
from flask import Blueprint, Response, request, jsonify
from flask_socketio import emit

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.utils.db import query
from backend.middleware.auth_middleware import token_required
from testing.detection_engine import DetectionEngine

detection_bp = Blueprint("detection", __name__)

# ── Engine singleton ───────────────────────────────────────
_MODEL_PATHS = {
    "monaco": os.path.join(PROJECT_ROOT, os.environ.get("MONACO_MODEL_PATH", "models/monaco_best.pt")),
    "parle":  os.path.join(PROJECT_ROOT, os.environ.get("PARLE_MODEL_PATH",  "models/parle_best.pt")),
    "marie":  os.path.join(PROJECT_ROOT, os.environ.get("MARIE_MODEL_PATH",  "models/marie_best.pt")),
}
_CAM_INDEX = int(os.environ.get("CAMERA_INDEX", 0))

engine = DetectionEngine(_MODEL_PATHS, camera_index=_CAM_INDEX)

# ── State ──────────────────────────────────────────────────
_current_batch_id: int   = None
_current_user_id:  int   = None
_batch_state_lock         = threading.Lock()


def init_detection_socket(socketio):
    """Register all SocketIO handlers and give engine the socketio ref."""
    engine.set_socketio(socketio)

    @socketio.on("connect")
    def on_connect():
        emit("status", {
            "msg":           "Connected to BiscuitAI",
            "camera_active": engine.is_camera_active,
            "batch_active":  engine.is_batch_active,
            "loaded_brands": engine.loaded_brands,
            "active_brand":  engine.active_brand,
        })

    @socketio.on("disconnect")
    def on_disconnect():
        pass

    @socketio.on("start_camera")
    def on_start_camera():
        ok  = engine.start_camera()
        engine.set_socketio(socketio)   # re-register after possible reconnect
        emit("camera_status", {
            "active": ok,
            "error":  None if ok else "Cannot open camera — check CAMERA_INDEX in .env",
        })

    @socketio.on("stop_camera")
    def on_stop_camera():
        if engine.is_batch_active:
            _do_stop_batch(socketio)
        engine.stop_camera()
        emit("camera_status", {"active": False, "error": None})

    @socketio.on("start_batch")
    def on_start_batch(data):
        """
        data = { user_id: int, brand: "Monaco"|"Parle-G"|"Marie" }

        CRITICAL: brand is passed to engine.start_batch(brand, callback).
        Engine stores it as _active_brand — only that model runs.
        """
        global _current_batch_id, _current_user_id

        data    = data or {}
        user_id = data.get("user_id")
        brand   = data.get("brand", "Monaco")

        # Normalize brand from display name to model key
        brand_key = _brand_to_key(brand)

        with _batch_state_lock:
            if engine.is_batch_active:
                emit("batch_status", {
                    "active": True,
                    "error":  "Batch already running — stop it first.",
                })
                return

            if not engine.is_camera_active:
                emit("batch_status", {
                    "active": False,
                    "error":  "Start camera before starting a batch.",
                })
                return

            # Check model is loaded
            if brand_key not in engine.loaded_brands:
                emit("batch_status", {
                    "active": False,
                    "error":  f"Model for '{brand}' not loaded. Check models/ folder.",
                })
                return

            # Create DB batch record
            try:
                batch_id = query(
                    "INSERT INTO batches (user_id, brand, started_at) VALUES (%s, %s, %s)",
                    [user_id, brand, datetime.utcnow()],
                    fetch=False,
                )
                _current_batch_id = batch_id
                _current_user_id  = user_id
            except Exception as e:
                emit("batch_status", {"active": False, "error": f"DB error: {e}"})
                return

            # ── Pass brand to engine — only this model will run ──
            try:
                engine.start_batch(
                    brand=brand_key,
                    log_callback=lambda payload: _on_detection(payload, socketio),
                )
            except Exception as e:
                emit("batch_status", {"active": False, "error": str(e)})
                return

        emit("batch_status", {
            "active":      True,
            "batch_id":    batch_id,
            "brand":       brand,
            "brand_key":   brand_key,
            "error":       None,
        })

    @socketio.on("stop_batch")
    def on_stop_batch():
        _do_stop_batch(socketio)


def _brand_to_key(brand: str) -> str:
    """
    Convert display brand name to model dict key.
    'Monaco' → 'monaco'
    'Parle-G' → 'parle'
    'Marie'  → 'marie'
    """
    mapping = {
        "monaco":  "monaco",
        "parle-g": "parle",
        "parleg":  "parle",
        "parle":   "parle",
        "marie":   "marie",
    }
    return mapping.get(brand.lower().replace(" ", ""), brand.lower())


def _do_stop_batch(socketio):
    global _current_batch_id

    with _batch_state_lock:
        if not engine.is_batch_active:
            socketio.emit("batch_status", {
                "active":  False,
                "error":   "No active batch",
                "summary": None,
            })
            return

        summary  = engine.stop_batch()
        counts   = summary.get("counts", {})
        batch_id = _current_batch_id

        if batch_id:
            try:
                query(
                    """UPDATE batches
                       SET ended_at=%s, total_count=%s,
                           good_count=%s, broken_count=%s, burnt_count=%s
                       WHERE id=%s""",
                    [
                        datetime.utcnow(),
                        counts.get("total",  0),
                        counts.get("Good",   0),
                        counts.get("Broken", 0),
                        counts.get("Burnt",  0),
                        batch_id,
                    ],
                    fetch=False,
                )
            except Exception as e:
                import logging
                logging.getLogger("detection_engine").error(f"DB update batch: {e}")

        _current_batch_id = None

    socketio.emit("batch_status", {
        "active":   False,
        "batch_id": batch_id,
        "summary":  summary,
        "error":    None,
    })


def _on_detection(payload: dict, socketio):
    """Called in DBLog thread when a confirmed detection pair is ready."""
    global _current_batch_id
    batch_id = _current_batch_id
    if not batch_id:
        return

    for i, det in enumerate(payload.get("detections", []), start=1):
        try:
            query(
                """INSERT INTO detections
                   (batch_id, biscuit_index, brand, quality, confidence,
                    bbox_x1, bbox_y1, bbox_x2, bbox_y2, inference_ms, detected_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                [
                    batch_id, i,
                    det.get("brand",      "Unknown"),
                    det.get("class",      "Unknown"),
                    round(det.get("confidence", 0.0), 4),
                    det["bbox"][0], det["bbox"][1],
                    det["bbox"][2], det["bbox"][3],
                    payload.get("inference_ms", 0),
                    payload.get("timestamp", datetime.utcnow().isoformat()),
                ],
                fetch=False,
            )
        except Exception as e:
            import logging
            logging.getLogger("detection_engine").error(f"DB insert detection: {e}")

        try:
            query(
                "CALL upsert_hourly_stats(%s, %s, %s)",
                [det.get("brand"), det.get("class"), payload.get("timestamp")],
                fetch=False,
            )
        except Exception:
            pass

    try:
        socketio.emit("detection_result", payload)
    except Exception:
        pass


# ── REST endpoints ─────────────────────────────────────────

@detection_bp.route("/status", methods=["GET"])
@token_required
def status():
    return jsonify({
        "camera_active": engine.is_camera_active,
        "batch_active":  engine.is_batch_active,
        "active_brand":  engine.active_brand,
        "loaded_brands": engine.loaded_brands,
        "batch_counts":  engine.batch_counts,
        "batch_id":      _current_batch_id,
    })


@detection_bp.route("/stream")
def mjpeg_stream():
    """MJPEG fallback — open http://localhost:5000/api/detection/stream in browser."""
    def gen():
        import time
        while True:
            jpeg = engine.get_frame_jpeg()
            if jpeg:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n"
                    + jpeg + b"\r\n"
                )
            time.sleep(0.04)
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")