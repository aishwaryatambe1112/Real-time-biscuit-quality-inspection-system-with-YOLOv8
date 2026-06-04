"""
backend/routes/users.py
Admin-only user management.
  GET    /api/users/           — list all users
  POST   /api/users/           — create user
  PATCH  /api/users/<id>       — toggle active / change role
  DELETE /api/users/<id>       — delete user
"""
from flask import Blueprint, request, jsonify
from backend.utils.db import query
from backend.middleware.auth_middleware import admin_required

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
@admin_required
def list_users():
    rows = query(
        "SELECT id, email, name, role, is_active, created_at FROM users ORDER BY created_at DESC"
    )
    for r in rows:
        r["created_at"] = str(r["created_at"])
    return jsonify(rows)


@users_bp.route("/", methods=["POST"])
@admin_required
def create_user():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    name  = (data.get("name")  or "").strip()
    role  = data.get("role", "operator")

    if not email or not name:
        return jsonify({"error": "email and name are required"}), 400
    if role not in ("admin", "operator"):
        return jsonify({"error": "role must be admin or operator"}), 400

    existing = query("SELECT id FROM users WHERE email=%s", [email])
    if existing:
        return jsonify({"error": "Email already registered"}), 409

    uid = query(
        "INSERT INTO users (email, name, role) VALUES (%s, %s, %s)",
        [email, name, role], fetch=False
    )
    return jsonify({"id": uid, "email": email, "name": name, "role": role}), 201


@users_bp.route("/<int:user_id>", methods=["PATCH"])
@admin_required
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    rows = query("SELECT id FROM users WHERE id=%s", [user_id])
    if not rows:
        return jsonify({"error": "User not found"}), 404

    if "is_active" in data:
        query("UPDATE users SET is_active=%s WHERE id=%s",
              [bool(data["is_active"]), user_id], fetch=False)
    if "role" in data and data["role"] in ("admin", "operator"):
        query("UPDATE users SET role=%s WHERE id=%s",
              [data["role"], user_id], fetch=False)
    if "name" in data and data["name"].strip():
        query("UPDATE users SET name=%s WHERE id=%s",
              [data["name"].strip(), user_id], fetch=False)

    updated = query("SELECT id,email,name,role,is_active FROM users WHERE id=%s", [user_id])
    return jsonify(updated[0])


@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
def delete_user(user_id):
    # Prevent self-deletion
    if user_id == request.user_id:
        return jsonify({"error": "Cannot delete yourself"}), 400
    rows = query("SELECT id FROM users WHERE id=%s", [user_id])
    if not rows:
        return jsonify({"error": "User not found"}), 404
    query("DELETE FROM users WHERE id=%s", [user_id], fetch=False)
    return jsonify({"deleted": True})
