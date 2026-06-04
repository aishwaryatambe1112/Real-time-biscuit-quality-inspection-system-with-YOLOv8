"""
=============================================================
BiscuitAI — Detection Engine v4  (Brand-Filtered)
=============================================================

KEY FIX — Label Mismatch:
  ROOT CAUSE: start_batch() never stored which brand was selected.
  In _inference_loop, `snap = dict(self._models)` always took
  ALL 3 models regardless of what the user picked in the dropdown.
  Result: Monaco frame → all 3 models fire → Marie/Parle labels
  appear on Monaco biscuits.

  FIX:
    1. start_batch(brand, log_callback) now accepts the brand name.
    2. self._active_brand stores the selected brand.
    3. _inference_loop: snap = {brand: self._models[brand]}
       → ONLY the selected model runs on every frame.
    4. All 3 models are still loaded at startup for fast switching,
       but only ONE runs inference per batch session.

Threading (unchanged, 7 threads):
  T1 CamCapture  — reads cam 30fps
  T2 FramePush   — JPEG → SocketIO  ~25fps  (independent of inference)
  T3 Inference   — coordinator, reads _infer_q
  T4 ModelWorker — only selected brand model runs (ThreadPoolExecutor)
  T5 DBLog       — fire-and-forget DB write per confirmed detection
=============================================================
"""

import cv2
import os
import time
import threading
import queue
import logging
import base64
import traceback
from concurrent.futures import ThreadPoolExecutor, Future, wait as futures_wait, ALL_COMPLETED
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Dict, List
import numpy as np

# ── Logger ────────────────────────────────────────────────
logger = logging.getLogger("detection_engine")
if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    ))
    logger.addHandler(_h)
logger.setLevel(logging.INFO)

# ── YOLO ──────────────────────────────────────────────────
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    logger.info("Ultralytics YOLO available")
except ImportError:
    YOLO_AVAILABLE = False
    logger.error("ultralytics NOT found — pip install ultralytics")

# ══════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════

# Per-model confidence thresholds.
# Lower = detects more (including broken/burnt which score lower).
# Monaco needs lowest because it has fewest training images.
MODEL_CONF = {
    "monaco": float(os.environ.get("MONACO_CONF", 0.28)),
    "parle":  float(os.environ.get("PARLE_CONF",  0.32)),
    "marie":  float(os.environ.get("MARIE_CONF",  0.30)),
}
DEFAULT_CONF    = float(os.environ.get("CONFIDENCE_THRESHOLD", 0.30))
IOU_NMS         = float(os.environ.get("IOU_THRESHOLD", 0.45))

# Expected biscuits per frame (exactly 2)
EXPECTED_COUNT  = 2

# Stability: N consecutive frames must agree before DB log
STABILITY_FRAMES = 3

# ── False-positive filter ─────────────────────────────────
MAX_ASPECT_RATIO = 3.5   # broken pieces can be elongated
MIN_AREA_FRAC    = 0.004  # 0.4% — catches small broken fragments
MAX_AREA_FRAC    = 0.15   # 15% — blocks faces close to camera
EDGE_PX          = 3      # ignore boxes touching frame edge

# ── Performance ───────────────────────────────────────────
FRAME_SKIP       = int(os.environ.get("FRAME_SKIP", 2))
JPEG_Q           = int(os.environ.get("JPEG_QUALITY", 75))
MODEL_WAIT_SEC   = 5.0   # generous timeout for slower hardware

# ── Brand / Class mappings ────────────────────────────────
CLASS_NAMES    = ["Broken", "Burnt", "Good"]
BISCUIT_BRANDS = {"monaco": "Monaco", "parle": "Parle-G", "marie": "Marie"}
COLOR_MAP      = {
    "Good":    (57,  255,  20),
    "Broken":  (0,   165, 255),
    "Burnt":   (0,     0, 220),
    "Unknown": (160, 160, 160),
}
FONT       = cv2.FONT_HERSHEY_SIMPLEX
FONT_SCALE = 0.54
FONT_THICK = 1


# ══════════════════════════════════════════════════════════
# Geometry helpers
# ══════════════════════════════════════════════════════════

def _iou(a: List[float], b: List[float]) -> float:
    ix1 = max(a[0], b[0]);  iy1 = max(a[1], b[1])
    ix2 = min(a[2], b[2]);  iy2 = min(a[3], b[3])
    iw  = max(0.0, ix2 - ix1)
    ih  = max(0.0, iy2 - iy1)
    inter = iw * ih
    if inter == 0.0:
        return 0.0
    aa = max(0.0, a[2]-a[0]) * max(0.0, a[3]-a[1])
    ab = max(0.0, b[2]-b[0]) * max(0.0, b[3]-b[1])
    return inter / (aa + ab - inter + 1e-7)


def _passes_filter(
    box: List[float], conf: float,
    frame_w: int, frame_h: int, conf_thresh: float
) -> bool:
    """Heuristic: is this box a biscuit and not a face/hand/background?"""
    if conf < conf_thresh:
        return False
    x1, y1, x2, y2 = box
    bw = max(0.0, x2 - x1)
    bh = max(0.0, y2 - y1)
    if bw < 1 or bh < 1:
        return False
    if x1 < EDGE_PX or y1 < EDGE_PX:
        return False
    if x2 > (frame_w - EDGE_PX) or y2 > (frame_h - EDGE_PX):
        return False
    area_frac = (bw * bh) / (frame_w * frame_h + 1e-6)
    if area_frac < MIN_AREA_FRAC or area_frac > MAX_AREA_FRAC:
        return False
    ratio = max(bw, bh) / (min(bw, bh) + 1e-6)
    if ratio > MAX_ASPECT_RATIO:
        return False
    return True


def _nms(dets: List[dict]) -> List[dict]:
    """Standard NMS — suppress overlapping boxes, keep highest confidence."""
    if not dets:
        return []
    sorted_dets = sorted(dets, key=lambda d: -d["confidence"])
    kept  = []
    used  = [False] * len(sorted_dets)
    for i, det_i in enumerate(sorted_dets):
        if used[i]:
            continue
        kept.append(det_i)
        for j in range(i + 1, len(sorted_dets)):
            if used[j]:
                continue
            if _iou(det_i["bbox"], sorted_dets[j]["bbox"]) >= 0.35:
                used[j] = True
    return kept


# ══════════════════════════════════════════════════════════
# DetectionEngine
# ══════════════════════════════════════════════════════════

class DetectionEngine:
    """
    Brand-filtered multi-model detection engine.

    All 3 models loaded at startup.
    Only the model matching start_batch(brand=...) runs per session.
    """

    def __init__(self, model_paths: Dict[str, str], camera_index: int = 0):
        self.model_paths   = {k: Path(v) for k, v in model_paths.items()}
        self.camera_index  = camera_index

        # Models (all 3 loaded at startup)
        self._models:       Dict[str, "YOLO"] = {}
        self._models_lock   = threading.RLock()

        # ── KEY FIX: active brand tracking ───────────────
        self._active_brand: Optional[str] = None   # set by start_batch()

        # Camera
        self._cap           = None
        self._cap_lock      = threading.Lock()
        self._cam_running   = threading.Event()
        self._cam_thread:   Optional[threading.Thread] = None

        # Two separate queues — camera NEVER blocked by inference
        self._raw_q:    queue.Queue = queue.Queue(maxsize=1)  # camera → push
        self._infer_q:  queue.Queue = queue.Queue(maxsize=1)  # camera → inference

        # JPEG for HTTP MJPEG fallback
        self._latest_jpeg  = None
        self._jpeg_lock    = threading.Lock()

        # Push thread
        self._push_thread: Optional[threading.Thread] = None
        self._push_running = threading.Event()
        self._socketio_ref = None

        # Annotated frame shared between inference → push thread
        self._annotated_frame      = None
        self._annotated_frame_lock = threading.Lock()

        # Batch / inference
        self._batch_active  = False
        self._batch_start:  Optional[datetime] = None
        self._log_callback: Optional[Callable] = None
        self._infer_running = threading.Event()
        self._infer_thread: Optional[threading.Thread] = None

        # Stability buffer
        self._stab_buf:  List[List[dict]] = []
        self._stab_lock  = threading.Lock()

        # Batch counters
        self._counts      = {"Good": 0, "Broken": 0, "Burnt": 0, "total": 0}
        self._counts_lock = threading.Lock()

        # 3-worker pool (one per model max)
        self._pool = ThreadPoolExecutor(
            max_workers=3, thread_name_prefix="ModelWorker"
        )

        # Load all models at startup
        logger.info("=" * 54)
        logger.info("  BiscuitAI — Loading all 3 models")
        logger.info("=" * 54)
        self._preload_all()
        logger.info("=" * 54)
        logger.info(f"  Loaded: {list(self._models.keys())}")
        logger.info("=" * 54)

    # ══════════════════════════════════════════════════════
    # Model loading
    # ══════════════════════════════════════════════════════

    def _preload_all(self):
        threads = []
        for brand in self.model_paths:
            t = threading.Thread(
                target=self._load_model, args=(brand,),
                daemon=True, name=f"Load-{brand}",
            )
            t.start()
            threads.append((brand, t))
        for brand, t in threads:
            t.join(timeout=300)
            if t.is_alive():
                logger.error(f"[{brand}] load timeout")

    def _load_model(self, brand: str):
        brand = brand.lower()
        path  = self.model_paths.get(brand)
        if not path or not path.exists():
            logger.error(f"[{brand}] NOT FOUND: {path}")
            return
        if not YOLO_AVAILABLE:
            return
        mb = path.stat().st_size / (1024 * 1024)
        logger.info(f"[{brand}] Loading {path.name} ({mb:.1f} MB) ...")
        try:
            t0 = time.perf_counter()
            m  = YOLO(str(path))
            m.overrides["verbose"] = False
            m.overrides["iou"]     = IOU_NMS
            m.overrides["max_det"] = 20
            # Two warm-up passes so first real frame is instant
            dummy = np.zeros((480, 640, 3), dtype=np.uint8)
            m(dummy, verbose=False, conf=0.01)
            m(dummy, verbose=False, conf=0.01)
            ms = (time.perf_counter() - t0) * 1000
            logger.info(f"[{brand}] ✓ Ready in {ms:.0f} ms")
            with self._models_lock:
                self._models[brand] = m
        except Exception as e:
            logger.error(f"[{brand}] load error: {e}")
            traceback.print_exc()

    @property
    def loaded_brands(self) -> List[str]:
        with self._models_lock:
            return list(self._models.keys())

    # ══════════════════════════════════════════════════════
    # Camera
    # ══════════════════════════════════════════════════════

    def start_camera(self) -> bool:
        if self._cam_running.is_set():
            return True
        cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            logger.error(f"Cannot open camera {self.camera_index}")
            return False
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS,          30)
        cap.set(cv2.CAP_PROP_BUFFERSIZE,   1)
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        logger.info(f"Camera: {w}x{h} @ {fps:.0f}fps")
        with self._cap_lock:
            self._cap = cap
        self._cam_running.set()
        self._cam_thread = threading.Thread(
            target=self._cam_loop, daemon=True, name="CamCapture"
        )
        self._cam_thread.start()
        self._push_running.set()
        self._push_thread = threading.Thread(
            target=self._push_loop, daemon=True, name="FramePush"
        )
        self._push_thread.start()
        logger.info("Camera + FramePush started")
        return True

    def stop_camera(self):
        self._cam_running.clear()
        self._push_running.clear()
        for t in [self._cam_thread, self._push_thread]:
            if t and t.is_alive():
                t.join(timeout=3.0)
        with self._cap_lock:
            if self._cap:
                self._cap.release()
                self._cap = None
        for q in [self._raw_q, self._infer_q]:
            while not q.empty():
                try: q.get_nowait()
                except queue.Empty: break
        logger.info("Camera stopped")

    def _cam_loop(self):
        """
        Reads frames at full 30fps.
        _raw_q  → every frame  → FramePush (display, always smooth)
        _infer_q → every FRAME_SKIP-th frame → Inference
        These are SEPARATE queues. Inference never delays display.
        """
        skip = 0
        fails = 0
        while self._cam_running.is_set():
            with self._cap_lock:
                cap = self._cap
            if not cap:
                time.sleep(0.01)
                continue
            ret, frame = cap.read()
            if not ret:
                fails += 1
                if fails > 60:
                    logger.error("Camera failed 60× — stopping")
                    self._cam_running.clear()
                    break
                time.sleep(0.01)
                continue
            fails = 0

            # Always push to display queue (raw, unmodified)
            if self._raw_q.full():
                try: self._raw_q.get_nowait()
                except queue.Empty: pass
            try: self._raw_q.put_nowait(frame)
            except queue.Full: pass

            # Push to inference queue only every FRAME_SKIP frames
            skip += 1
            if skip >= FRAME_SKIP:
                skip = 0
                if self._infer_q.full():
                    try: self._infer_q.get_nowait()
                    except queue.Empty: pass
                try: self._infer_q.put_nowait(frame)
                except queue.Full: pass

    def _push_loop(self):
        """
        Reads raw frames from _raw_q.
        If inference has produced an annotated frame, uses that instead.
        Encodes JPEG and pushes to SocketIO.
        Runs independently — camera display is NEVER blocked by inference.
        """
        while self._push_running.is_set():
            try:
                frame = self._raw_q.get(timeout=0.05)
            except queue.Empty:
                continue

            # Use annotated frame if fresh inference result exists
            ann = self._get_annotated()
            if ann is not None:
                frame = ann

            try:
                ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_Q])
                if not ok:
                    continue
                jpeg = buf.tobytes()
            except Exception:
                continue

            with self._jpeg_lock:
                self._latest_jpeg = jpeg

            if self._socketio_ref:
                try:
                    b64 = base64.b64encode(jpeg).decode("utf-8")
                    self._socketio_ref.emit("frame", {"data": b64})
                except Exception as e:
                    logger.debug(f"SocketIO push: {e}")

    def _set_annotated(self, frame: np.ndarray):
        with self._annotated_frame_lock:
            self._annotated_frame = frame

    def _get_annotated(self) -> Optional[np.ndarray]:
        with self._annotated_frame_lock:
            return self._annotated_frame

    def set_socketio(self, sio):
        self._socketio_ref = sio

    # ══════════════════════════════════════════════════════
    # Batch — KEY FIX: accepts brand parameter
    # ══════════════════════════════════════════════════════

    def start_batch(self, brand: str, log_callback: Callable):
        """
        Start an inspection batch for a SPECIFIC brand.

        Parameters
        ----------
        brand : str
            'monaco' | 'parle' | 'marie'  (case-insensitive)
        log_callback : Callable
            Called with detection payload when a stable detection is confirmed.
        """
        brand = brand.lower()

        # Map display names back to keys
        brand_alias = {"parle-g": "parle", "parleg": "parle"}
        brand = brand_alias.get(brand, brand)

        with self._models_lock:
            if brand not in self._models:
                available = list(self._models.keys())
                raise RuntimeError(
                    f"Model for '{brand}' not loaded. "
                    f"Available: {available}. "
                    f"Check models/ folder."
                )

        if self._batch_active:
            raise RuntimeError("Batch already active — stop it first")
        if not self._cam_running.is_set():
            raise RuntimeError("Start camera before starting batch")

        # ── Store active brand — ONLY THIS MODEL WILL RUN ──
        self._active_brand = brand
        logger.info(f"Active brand set to: '{brand}' — only this model will run")

        self._log_callback  = log_callback
        self._batch_active  = True
        self._batch_start   = datetime.utcnow()

        with self._stab_lock:
            self._stab_buf.clear()
        with self._counts_lock:
            self._counts = {"Good": 0, "Broken": 0, "Burnt": 0, "total": 0}

        # Clear annotated frame from any previous batch
        self._set_annotated(None)

        self._infer_running.set()
        self._infer_thread = threading.Thread(
            target=self._inference_loop,
            daemon=True, name="Inference",
        )
        self._infer_thread.start()
        logger.info(
            f"Batch started | brand='{brand}' "
            f"| conf_thresh={MODEL_CONF.get(brand, DEFAULT_CONF)}"
        )

    def stop_batch(self) -> dict:
        self._infer_running.clear()
        self._batch_active = False

        if self._infer_thread and self._infer_thread.is_alive():
            self._infer_thread.join(timeout=8.0)

        with self._counts_lock:
            counts = dict(self._counts)

        brand = self._active_brand
        self._active_brand = None
        self._log_callback = None
        self._set_annotated(None)

        summary = {
            "start_time": self._batch_start.isoformat() if self._batch_start else None,
            "end_time":   datetime.utcnow().isoformat(),
            "brand":      brand,
            "counts":     counts,
        }
        logger.info(f"Batch stopped | brand='{brand}' | {counts}")
        return summary

    # ══════════════════════════════════════════════════════
    # Inference loop — runs ONLY selected brand model
    # ══════════════════════════════════════════════════════

    def _inference_loop(self):
        """
        Pulls frames from _infer_q.
        Runs ONLY the selected brand's model (self._active_brand).
        No other model fires — zero cross-brand contamination.
        """
        frames_done = 0
        logged      = 0

        brand = self._active_brand   # snapshot at batch start
        if not brand:
            logger.error("_inference_loop: no active brand set")
            return

        logger.info(f"Inference loop running — brand={brand}")

        while self._infer_running.is_set():
            try:
                frame = self._infer_q.get(timeout=0.5)
            except queue.Empty:
                continue

            fh, fw = frame.shape[:2]
            t0     = time.perf_counter()

            # ── Run ONLY the selected model ────────────────
            with self._models_lock:
                model = self._models.get(brand)

            if model is None:
                logger.error(f"Model for '{brand}' disappeared from registry")
                continue

            # Submit single model to thread pool
            future = self._pool.submit(self._run_one_model, brand, model, frame)

            # Wait for result with generous timeout
            done, not_done = futures_wait(
                [future], timeout=MODEL_WAIT_SEC, return_when=ALL_COMPLETED
            )

            if not_done:
                logger.warning(f"[{brand}] inference timed out after {MODEL_WAIT_SEC}s")
                future.cancel()
                continue

            inf_ms = (time.perf_counter() - t0) * 1000

            # ── Collect raw detections ─────────────────────
            raw_dets: List[dict] = []
            try:
                raw_dets = future.result(timeout=0.1)
            except Exception as e:
                logger.warning(f"[{brand}] result error: {e}")
                continue

            # ── Heuristic filter ───────────────────────────
            conf_thresh = MODEL_CONF.get(brand, DEFAULT_CONF)
            valid = [
                d for d in raw_dets
                if _passes_filter(d["bbox"], d["confidence"], fw, fh, conf_thresh)
            ]

            # ── NMS within same model output ───────────────
            merged = _nms(valid)

            # ── Annotate frame and store for display ───────
            annotated = self._draw(frame.copy(), merged, inf_ms, brand)
            self._set_annotated(annotated)

            frames_done += 1

            # ── Stability check ────────────────────────────
            count = len(merged)
            if count == EXPECTED_COUNT:
                with self._stab_lock:
                    self._stab_buf.append(merged)
                    self._stab_buf = self._stab_buf[-STABILITY_FRAMES:]
                    buf = list(self._stab_buf)

                if len(buf) == STABILITY_FRAMES and self._is_stable(buf):
                    confirmed = buf[-1]
                    with self._stab_lock:
                        self._stab_buf.clear()
                    logged += 1
                    tags = ", ".join(
                        f"{d['brand']} {d['class']} {d['confidence']:.0%}"
                        for d in confirmed
                    )
                    logger.info(f"✓ #{logged} | {brand} | {inf_ms:.0f}ms | {tags}")
                    self._emit(confirmed, inf_ms)
            else:
                with self._stab_lock:
                    if self._stab_buf:
                        self._stab_buf.clear()

        logger.info(f"Inference done | brand={brand} | frames={frames_done} logged={logged}")

    def _run_one_model(
        self, brand: str, model: "YOLO", frame: np.ndarray
    ) -> List[dict]:
        """Run one model, return raw detection dicts."""
        conf_thresh = MODEL_CONF.get(brand, DEFAULT_CONF)
        try:
            results = model(frame, verbose=False, conf=conf_thresh)[0]
        except Exception as e:
            logger.error(f"[{brand}] model() error: {e}")
            return []

        if results.boxes is None or len(results.boxes) == 0:
            return []

        dets   = []
        boxes  = results.boxes.xyxy.cpu().numpy()
        confs  = results.boxes.conf.cpu().numpy()
        labels = results.boxes.cls.cpu().numpy().astype(int)

        for box, conf, lbl in zip(boxes, confs, labels):
            cls_name = CLASS_NAMES[lbl] if 0 <= lbl < len(CLASS_NAMES) else "Unknown"
            dets.append({
                "brand":      BISCUIT_BRANDS.get(brand, brand),
                "brand_key":  brand,
                "class":      cls_name,
                "confidence": float(conf),
                "bbox":       box.tolist(),
            })
        return dets

    # ══════════════════════════════════════════════════════
    # Stability
    # ══════════════════════════════════════════════════════

    def _is_stable(self, buf: List[List[dict]]) -> bool:
        def sig(dets):
            return tuple(sorted((d["brand"], d["class"]) for d in dets))
        ref_sig   = sig(buf[0])
        ref_count = len(buf[0])
        for dets in buf[1:]:
            if len(dets) != ref_count or sig(dets) != ref_sig:
                return False
        return True

    # ══════════════════════════════════════════════════════
    # Emit
    # ══════════════════════════════════════════════════════

    def _emit(self, detections: List[dict], inf_ms: float):
        with self._counts_lock:
            self._counts["total"] += len(detections)
            for d in detections:
                cls = d["class"]
                if cls in self._counts:
                    self._counts[cls] += 1
        if self._log_callback is None:
            return
        payload = {
            "detections":   detections,
            "timestamp":    datetime.utcnow().isoformat(),
            "inference_ms": round(inf_ms, 1),
        }
        threading.Thread(
            target=self._safe_callback,
            args=(payload,), daemon=True, name="DBLog"
        ).start()

    def _safe_callback(self, payload: dict):
        try:
            self._log_callback(payload)
        except Exception as e:
            logger.error(f"log_callback error: {e}")

    # ══════════════════════════════════════════════════════
    # Drawing
    # ══════════════════════════════════════════════════════

    def _draw(
        self, frame: np.ndarray,
        dets: List[dict], inf_ms: float,
        brand: str
    ) -> np.ndarray:
        h, w = frame.shape[:2]
        brand_display = BISCUIT_BRANDS.get(brand, brand)

        for det in dets:
            x1, y1, x2, y2 = [int(v) for v in det["bbox"]]
            cls   = det["class"]
            conf  = det["confidence"]
            color = COLOR_MAP.get(cls, (200, 200, 200))

            x1 = max(0, min(w-1, x1));  y1 = max(0, min(h-1, y1))
            x2 = max(0, min(w-1, x2));  y2 = max(0, min(h-1, y2))

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            label = f"{brand_display}  |  {cls}  |  {conf:.0%}"
            (tw, th), _ = cv2.getTextSize(label, FONT, FONT_SCALE, FONT_THICK)
            pad  = 4
            by1  = max(0, y1 - th - 2*pad)
            bx2  = min(w, x1 + tw + 2*pad)
            cv2.rectangle(frame, (x1, by1), (bx2, y1), color, -1)
            cv2.putText(frame, label, (x1+pad, y1-pad),
                        FONT, FONT_SCALE, (255,255,255), FONT_THICK, cv2.LINE_AA)
            cv2.circle(frame, (x2-8, y2-8), 5, color, -1)

        # Overlays
        cv2.putText(frame, f"Inf: {inf_ms:.0f}ms", (8, 22),
                    FONT, 0.55, (0,255,255), 1, cv2.LINE_AA)

        count    = len(dets)
        ok       = (count == EXPECTED_COUNT)
        cnt_col  = (57,255,20) if ok else (0,120,255)
        cv2.putText(frame, f"Det: {count}/{EXPECTED_COUNT}", (8, 44),
                    FONT, 0.55, cnt_col, 1, cv2.LINE_AA)

        # Brand watermark — shows which model is active
        cv2.putText(frame, f"Model: {brand_display}", (8, 66),
                    FONT, 0.50, (200,200,0), 1, cv2.LINE_AA)

        # Batch status badge top-right
        st_txt = "BATCH LIVE" if self._batch_active else "BATCH OFF"
        st_col = (57,255,20)  if self._batch_active else (0,80,200)
        (stw, sth), _ = cv2.getTextSize(st_txt, FONT, 0.52, 1)
        cv2.rectangle(frame, (w-stw-14, 6), (w-4, 28), st_col, -1)
        cv2.putText(frame, st_txt, (w-stw-10, 23),
                    FONT, 0.52, (0,0,0), 1, cv2.LINE_AA)
        return frame

    # ══════════════════════════════════════════════════════
    # Output
    # ══════════════════════════════════════════════════════

    def get_frame_jpeg(self) -> Optional[bytes]:
        with self._jpeg_lock:
            return self._latest_jpeg

    def get_frame_b64(self) -> Optional[str]:
        j = self.get_frame_jpeg()
        return base64.b64encode(j).decode() if j else None

    @property
    def is_camera_active(self) -> bool:
        return self._cam_running.is_set()

    @property
    def is_batch_active(self) -> bool:
        return self._batch_active

    @property
    def active_brand(self) -> Optional[str]:
        return self._active_brand

    @property
    def batch_counts(self) -> dict:
        with self._counts_lock:
            return dict(self._counts)

    def shutdown(self):
        if self._batch_active:
            self.stop_batch()
        if self._cam_running.is_set():
            self.stop_camera()
        self._pool.shutdown(wait=False, cancel_futures=True)
        logger.info("Engine shutdown complete")