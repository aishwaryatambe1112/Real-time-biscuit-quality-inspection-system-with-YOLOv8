"""
backend/routes/dashboard.py
Analytics endpoints for charts & KPIs.
"""
from flask import Blueprint, request, jsonify
from backend.utils.db import query
from backend.middleware.auth_middleware import token_required

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/summary", methods=["GET"])
@token_required
def summary():
    """Overall KPI cards."""
    totals = query(
        """SELECT brand,
                  SUM(total_count) AS total,
                  SUM(good_count)  AS good,
                  SUM(broken_count) AS broken,
                  SUM(burnt_count)  AS burnt
           FROM batches GROUP BY brand"""
    )
    overall = query(
        """SELECT SUM(total_count) AS total, SUM(good_count) AS good,
                  SUM(broken_count) AS broken, SUM(burnt_count) AS burnt
           FROM batches"""
    )[0]
    batch_count = query("SELECT COUNT(*) AS cnt FROM batches")[0]["cnt"]
    return jsonify({
        "by_brand":    totals,
        "overall":     overall,
        "batch_count": batch_count,
    })


@dashboard_bp.route("/trend", methods=["GET"])
@token_required
def trend():
    """Hourly trend data for time-series charts."""
    brand  = request.args.get("brand")
    hours  = int(request.args.get("hours", 24))
    where  = "WHERE hour_bucket >= NOW() - INTERVAL %s HOUR"
    params = [hours]
    if brand:
        where += " AND brand=%s"; params.append(brand)

    rows = query(
        f"""SELECT brand, hour_bucket, total_count, good_count, broken_count, burnt_count
            FROM hourly_stats {where} ORDER BY hour_bucket""",
        params
    )
    return jsonify(rows)


@dashboard_bp.route("/defect-rate", methods=["GET"])
@token_required
def defect_rate():
    """Defect (Broken+Burnt) vs Good per brand."""
    rows = query(
        """SELECT brand,
                  SUM(good_count)              AS good,
                  SUM(broken_count+burnt_count) AS defect,
                  SUM(total_count)             AS total
           FROM batches WHERE total_count>0 GROUP BY brand"""
    )
    result = []
    for r in rows:
        t = r["total"] or 1
        result.append({
            "brand":        r["brand"],
            "good_pct":     round(r["good"]/t*100, 1),
            "defect_pct":   round(r["defect"]/t*100, 1),
            "broken_pct":   None,  # calculated below
            "burnt_pct":    None,
        })
    # Detailed breakdown
    detail = query(
        """SELECT brand,
                  SUM(broken_count) AS broken,
                  SUM(burnt_count)  AS burnt,
                  SUM(total_count)  AS total
           FROM batches WHERE total_count>0 GROUP BY brand"""
    )
    detail_map = {r["brand"]: r for r in detail}
    for r in result:
        d  = detail_map.get(r["brand"], {})
        t  = d.get("total") or 1
        r["broken_pct"] = round((d.get("broken") or 0)/t*100, 1)
        r["burnt_pct"]  = round((d.get("burnt")  or 0)/t*100, 1)
    return jsonify(result)


@dashboard_bp.route("/comparison", methods=["GET"])
@token_required
def comparison():
    """Side-by-side per-brand stats for comparison chart."""
    rows = query(
        """SELECT brand,
                  COUNT(*) AS batch_count,
                  SUM(total_count) AS total,
                  SUM(good_count)  AS good,
                  SUM(broken_count) AS broken,
                  SUM(burnt_count)  AS burnt,
                  AVG(total_count)  AS avg_per_batch
           FROM batches GROUP BY brand"""
    )
    return jsonify(rows)


@dashboard_bp.route("/recent-batches", methods=["GET"])
@token_required
def recent_batches():
    limit = int(request.args.get("limit", 10))
    rows  = query(
        """SELECT b.id, b.brand, b.started_at, b.ended_at,
                  b.total_count, b.good_count, b.broken_count, b.burnt_count,
                  u.name AS operator
           FROM batches b JOIN users u ON u.id=b.user_id
           ORDER BY b.started_at DESC LIMIT %s""",
        [limit]
    )
    return jsonify(rows)


@dashboard_bp.route("/live-counts", methods=["GET"])
@token_required
def live_counts():
    """Today's totals."""
    rows = query(
        """SELECT brand,
                  SUM(total_count) AS total,
                  SUM(good_count)  AS good,
                  SUM(broken_count) AS broken,
                  SUM(burnt_count)  AS burnt
           FROM batches
           WHERE DATE(started_at)=CURDATE()
           GROUP BY brand"""
    )
    return jsonify(rows)
