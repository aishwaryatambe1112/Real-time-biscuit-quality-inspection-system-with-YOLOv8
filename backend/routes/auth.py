"""
backend/routes/auth.py
OTP-based login:
  POST /api/auth/request-otp   { email }
  POST /api/auth/verify-otp    { email, otp }
  GET  /api/auth/me            (protected)
"""
import os, jwt, hashlib, random, string
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from backend.utils.db import query
from backend.middleware.auth_middleware import token_required
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint("auth", __name__)
SECRET  = os.environ.get("JWT_SECRET","dev-secret")
SG_KEY  = os.environ.get("SENDGRID_API_KEY","")
SG_FROM = os.environ.get("SENDGRID_SENDER_EMAIL","noreply@biscuitai.com")
SG_NAME = os.environ.get("SENDGRID_SENDER_NAME","BiscuitAI System")
OTP_EXPIRY_MINUTES = 10


def _gen_otp(length=6):
    return ''.join(random.choices(string.digits, k=length))

def _hash_otp(otp):
    return hashlib.sha256(otp.encode()).hexdigest()

def _send_otp_email(email: str, otp: str, name: str):
    msg = Mail(
        from_email=(SG_FROM, SG_NAME),
        to_emails=email,
        subject="Your BiscuitAI Login OTP",
        html_content=f"""
        <div style="font-family:Inter,sans-serif;max-width:480px;margin:auto;
                    background:#0f172a;color:#e2e8f0;padding:40px;border-radius:12px;">
            <h2 style="color:#f59e0b;margin-bottom:8px;">🍪 BiscuitAI</h2>
            <h3 style="color:#fff;">Real-Time Quality Inspection System</h3>
            <p>Hello <strong>{name}</strong>,</p>
            <p>Your one-time login code is:</p>
            <div style="font-size:36px;font-weight:700;letter-spacing:8px;
                        color:#f59e0b;background:#1e293b;padding:20px;
                        border-radius:8px;text-align:center;margin:20px 0;">
                {otp}
            </div>
            <p style="color:#94a3b8;font-size:13px;">
                This code expires in {OTP_EXPIRY_MINUTES} minutes.<br>
                Do not share this code with anyone.
            </p>
        </div>
        """
    )
    sg = SendGridAPIClient(SG_KEY)
    sg.send(msg)


@auth_bp.route("/request-otp", methods=["POST"])
def request_otp():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error":"Email required"}), 400

    users = query("SELECT id,name,role FROM users WHERE email=%s AND is_active=1", [email])
    if not users:
        return jsonify({"error":"Email not registered. Contact admin."}), 404

    user = users[0]
    otp  = _gen_otp()
    exp  = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

    # Invalidate old OTPs for this email
    query("UPDATE otp_tokens SET used=1 WHERE email=%s AND used=0", [email], fetch=False)
    # Insert new
    query(
        "INSERT INTO otp_tokens (email,otp_hash,expires_at) VALUES (%s,%s,%s)",
        [email, _hash_otp(otp), exp], fetch=False
    )

    try:
        _send_otp_email(email, otp, user["name"])
    except Exception as e:
        print(f"[SendGrid] Error: {e}")
        # In dev — return OTP directly (remove in production!)
        return jsonify({"message":"OTP sent (dev mode)", "dev_otp": otp}), 200

    return jsonify({"message":"OTP sent to your email", "expires_in": OTP_EXPIRY_MINUTES*60}), 200


@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data  = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    otp   = (data.get("otp")   or "").strip()
    if not email or not otp:
        return jsonify({"error":"Email and OTP required"}), 400

    now   = datetime.utcnow()
    rows  = query(
        "SELECT id,otp_hash,expires_at,used FROM otp_tokens "
        "WHERE email=%s AND used=0 ORDER BY created_at DESC LIMIT 1",
        [email]
    )
    if not rows:
        return jsonify({"error":"No active OTP. Request a new one."}), 400

    row = rows[0]
    if row["used"]:
        return jsonify({"error":"OTP already used"}), 400
    if datetime.strptime(str(row["expires_at"]),"%Y-%m-%d %H:%M:%S") < now:
        return jsonify({"error":"OTP expired"}), 400
    if row["otp_hash"] != _hash_otp(otp):
        return jsonify({"error":"Invalid OTP"}), 400

    # Mark used
    query("UPDATE otp_tokens SET used=1 WHERE id=%s", [row["id"]], fetch=False)

    users = query("SELECT id,name,email,role FROM users WHERE email=%s", [email])
    user  = users[0]

    token = jwt.encode({
        "user_id": user["id"],
        "email":   user["email"],
        "name":    user["name"],
        "role":    user["role"],
        "exp":     datetime.utcnow() + timedelta(hours=24),
    }, SECRET, algorithm="HS256")

    return jsonify({"token": token, "user": {
        "id":    user["id"],
        "name":  user["name"],
        "email": user["email"],
        "role":  user["role"],
    }}), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def me():
    users = query("SELECT id,name,email,role FROM users WHERE id=%s", [request.user_id])
    if not users:
        return jsonify({"error":"User not found"}), 404
    return jsonify(users[0]), 200
