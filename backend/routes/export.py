"""
backend/routes/export.py
GET /api/export/batches        — export all batches CSV
GET /api/export/detections     — export detections CSV (optional ?batch_id=)
"""
import csv, io
from flask import Blueprint, request, Response
from backend.utils.db import query
from backend.middleware.auth_middleware import token_required

export_bp = Blueprint("export", __name__)


def _csv_response(rows, filename):
    if not rows:
        return Response("No data", mimetype="text/plain")
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@export_bp.route("/batches", methods=["GET"])
@token_required
def export_batches():
    brand = request.args.get("brand")
    where = "WHERE 1=1"
    params = []
    if brand:
        where += " AND b.brand=%s"; params.append(brand)
    rows = query(
        f"""SELECT b.id, b.brand, u.name AS operator,
                   b.started_at, b.ended_at,
                   b.total_count, b.good_count, b.broken_count, b.burnt_count
            FROM batches b JOIN users u ON u.id=b.user_id
            {where} ORDER BY b.started_at DESC""",
        params
    )
    # Convert datetime to string
    for r in rows:
        r["started_at"] = str(r.get("started_at",""))
        r["ended_at"]   = str(r.get("ended_at",""))
    return _csv_response(rows, "batches_export.csv")


@export_bp.route("/detections", methods=["GET"])
@token_required
def export_detections():
    batch_id = request.args.get("batch_id")
    brand    = request.args.get("brand")
    where = "WHERE 1=1"
    params = []
    if batch_id:
        where += " AND d.batch_id=%s"; params.append(batch_id)
    if brand:
        where += " AND d.brand=%s"; params.append(brand)
    rows = query(
        f"""SELECT d.id, d.batch_id, d.brand, d.quality,
                   d.confidence, d.biscuit_index, d.inference_ms, d.detected_at
            FROM detections d {where}
            ORDER BY d.detected_at DESC LIMIT 50000""",
        params
    )
    for r in rows:
        r["detected_at"] = str(r.get("detected_at",""))
        r["confidence"]  = float(r.get("confidence",0))
    return _csv_response(rows, "detections_export.csv")
