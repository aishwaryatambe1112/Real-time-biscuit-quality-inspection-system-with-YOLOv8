"""
backend/routes/export.py
=========================
CSV export endpoints. Auth token can be passed as:
  - Authorization: Bearer <token>  header  (from React via axios)
  - ?token=<jwt>                   query param (direct browser download link)

Endpoints:
  GET /api/export/batches
        ?brand=Monaco|Parle-G|Marie   (optional filter)
        ?token=<jwt>                   (for direct browser download)

  GET /api/export/detections
        ?batch_id=<id>                 (optional: specific batch only)
        ?brand=Monaco|Parle-G|Marie   (optional: filter by brand)
        ?token=<jwt>                   (for direct browser download)
"""

import csv
import io
from datetime import datetime
from flask import Blueprint, request, Response
from backend.utils.db import query
from backend.middleware.auth_middleware import token_required

export_bp = Blueprint("export", __name__)


def _make_csv_response(rows: list, filename: str) -> Response:
    """
    Convert a list of dicts to a CSV file response.
    Returns a plain text response if no rows found.
    """
    if not rows:
        return Response(
            "No data found for the selected filters.",
            mimetype="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    buf = io.StringIO()
    # Use the keys from the first row as CSV headers
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)

    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


def _safe_str(val) -> str:
    """Convert datetime or None to plain string safely."""
    if val is None:
        return ""
    return str(val)


def _safe_float(val) -> float:
    """Convert confidence decimal to float safely."""
    try:
        return float(val)
    except (TypeError, ValueError):
        return 0.0


# ── Export all batches ─────────────────────────────────────

@export_bp.route("/batches", methods=["GET"])
@token_required
def export_batches():
    """
    Export batch history as CSV.
    Query params:
      brand   — filter by brand name (optional)
      token   — JWT for direct browser download (optional, used instead of header)
    """
    brand  = request.args.get("brand", "").strip()
    where  = "WHERE 1=1"
    params = []

    if brand:
        where += " AND b.brand = %s"
        params.append(brand)

    rows = query(
        f"""
        SELECT
            b.id            AS batch_id,
            b.brand,
            u.name          AS operator,
            b.started_at,
            b.ended_at,
            b.total_count,
            b.good_count,
            b.broken_count,
            b.burnt_count
        FROM batches b
        JOIN users u ON u.id = b.user_id
        {where}
        ORDER BY b.started_at DESC
        """,
        params,
    )

    # Convert datetimes to readable strings
    for r in rows:
        r["started_at"] = _safe_str(r.get("started_at"))
        r["ended_at"]   = _safe_str(r.get("ended_at"))

    # Build filename with timestamp
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix   = f"_{brand.lower().replace('-','')}" if brand else "_all"
    filename = f"batches{suffix}_{ts}.csv"

    return _make_csv_response(rows, filename)


# ── Export detections ──────────────────────────────────────

@export_bp.route("/detections", methods=["GET"])
@token_required
def export_detections():
    """
    Export detection events as CSV.
    Query params:
      batch_id — filter by specific batch (optional)
      brand    — filter by brand name (optional)
      token    — JWT for direct browser download (optional)
    """
    batch_id = request.args.get("batch_id", "").strip()
    brand    = request.args.get("brand",    "").strip()

    where  = "WHERE 1=1"
    params = []

    if batch_id:
        where += " AND d.batch_id = %s"
        params.append(batch_id)

    if brand:
        where += " AND d.brand = %s"
        params.append(brand)

    rows = query(
        f"""
        SELECT
            d.id,
            d.batch_id,
            d.brand,
            d.quality,
            d.confidence,
            d.biscuit_index,
            d.inference_ms,
            d.detected_at
        FROM detections d
        {where}
        ORDER BY d.detected_at DESC
        LIMIT 50000
        """,
        params,
    )

    # Normalise types
    for r in rows:
        r["detected_at"] = _safe_str(r.get("detected_at"))
        r["confidence"]  = round(_safe_float(r.get("confidence")), 4)
        r["inference_ms"] = round(_safe_float(r.get("inference_ms")), 1)

    # Build filename
    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    if batch_id:
        filename = f"detections_batch{batch_id}_{ts}.csv"
    elif brand:
        filename = f"detections_{brand.lower().replace('-','').replace(' ','')}_{ts}.csv"
    else:
        filename = f"detections_all_{ts}.csv"

    return _make_csv_response(rows, filename)