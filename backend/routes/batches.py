"""
backend/routes/batches.py
GET  /api/batches              — paginated batch history
GET  /api/batches/:id          — single batch + detections
"""
from flask import Blueprint, request, jsonify
from backend.utils.db import query
from backend.middleware.auth_middleware import token_required

batches_bp = Blueprint("batches", __name__)


@batches_bp.route("/", methods=["GET"])
@token_required
def list_batches():
    page     = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    brand    = request.args.get("brand")
    offset   = (page - 1) * per_page

    where = "WHERE 1=1"
    params = []
    if brand:
        where += " AND b.brand=%s"; params.append(brand)

    rows = query(
        f"""SELECT b.id, b.brand, b.started_at, b.ended_at,
                   b.total_count, b.good_count, b.broken_count, b.burnt_count,
                   u.name AS operator
            FROM batches b JOIN users u ON u.id=b.user_id
            {where}
            ORDER BY b.started_at DESC
            LIMIT %s OFFSET %s""",
        params + [per_page, offset]
    )

    total = query(f"SELECT COUNT(*) AS cnt FROM batches b {where}", params)[0]["cnt"]

    return jsonify({
        "batches":   rows,
        "total":     total,
        "page":      page,
        "per_page":  per_page,
        "pages":     (total + per_page - 1) // per_page,
    })


@batches_bp.route("/<int:batch_id>", methods=["GET"])
@token_required
def get_batch(batch_id):
    batches = query(
        """SELECT b.*, u.name AS operator FROM batches b
           JOIN users u ON u.id=b.user_id WHERE b.id=%s""",
        [batch_id]
    )
    if not batches:
        return jsonify({"error": "Batch not found"}), 404

    detections = query(
        """SELECT id, biscuit_index, brand, quality, confidence,
                  bbox_x1, bbox_y1, bbox_x2, bbox_y2, inference_ms, detected_at
           FROM detections WHERE batch_id=%s ORDER BY detected_at""",
        [batch_id]
    )
    return jsonify({"batch": batches[0], "detections": detections})
