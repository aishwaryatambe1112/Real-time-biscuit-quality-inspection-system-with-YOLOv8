"""
=============================================================
BiscuitAI — Flask + Flask-SocketIO Backend
=============================================================
Start with:  python backend/app.py
=============================================================
"""
import sys
import os
import atexit

# Ensure project root is on path so `testing` package resolves
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify
from flask_socketio import SocketIO
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

# ── Import blueprints ──────────────────────────────────────
from backend.routes.auth      import auth_bp
from backend.routes.detection import detection_bp, init_detection_socket, engine
from backend.routes.batches   import batches_bp
from backend.routes.dashboard import dashboard_bp
from backend.routes.export    import export_bp
from backend.routes.users     import users_bp
from backend.utils.db         import init_db

# ── Create app ────────────────────────────────────────────
app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("JWT_SECRET", "dev-secret-change-me")

# CORS — allow React dev server
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# SocketIO — threading mode for Windows compatibility
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading",
    logger=False,
    engineio_logger=False,
)

# ── Register blueprints ────────────────────────────────────
app.register_blueprint(auth_bp,      url_prefix="/api/auth")
app.register_blueprint(detection_bp, url_prefix="/api/detection")
app.register_blueprint(batches_bp,   url_prefix="/api/batches")
app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
app.register_blueprint(export_bp,    url_prefix="/api/export")
app.register_blueprint(users_bp,     url_prefix="/api/users")

# ── Register SocketIO events ───────────────────────────────
init_detection_socket(socketio)

# ── Graceful shutdown — release camera on Ctrl+C ──────────
@atexit.register
def _on_exit():
    try:
        engine.shutdown()
    except Exception:
        pass

# ── Health check ──────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({
        "status":        "ok",
        "service":       "BiscuitAI API",
        "camera_active": engine.is_camera_active,
        "batch_active":  engine.is_batch_active,
        "loaded_brands": engine.loaded_brands,
    })

# ── Global error handlers ──────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500

# ── Entry point ────────────────────────────────────────────
if __name__ == "__main__":
    print("\n" + "═" * 56)
    print("  🍪  BiscuitAI — Real-Time Quality Inspection System")
    print("═" * 56)

    # Initialise DB schema on first run
    try:
        init_db()
    except Exception as e:
        print(f"[WARNING] DB init: {e}")

    port = int(os.environ.get("BACKEND_PORT", 5000))
    print(f"  Server  : http://localhost:{port}")
    print(f"  Env     : {os.environ.get('NODE_ENV', 'development')}")
    print(f"  Models  : {engine.loaded_brands}")
    print("═" * 56 + "\n")

    socketio.run(
        app,
        host="0.0.0.0",
        port=port,
        debug=False,
        allow_unsafe_werkzeug=True,
        use_reloader=False,
    )