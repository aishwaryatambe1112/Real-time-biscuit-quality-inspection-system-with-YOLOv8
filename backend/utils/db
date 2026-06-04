"""
backend/utils/db.py — MySQL connection pool for Python backend
"""
import os, mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
load_dotenv()

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="biscuit_pool",
            pool_size=10,
            host=os.environ.get("DB_HOST","localhost"),
            port=int(os.environ.get("DB_PORT","3306")),
            database=os.environ.get("DB_NAME","biscuit_inspection"),
            user=os.environ.get("DB_USER","root"),
            password=os.environ.get("DB_PASSWORD",""),
            charset="utf8mb4",
            autocommit=True,
        )
    return _pool

def get_conn():
    return get_pool().get_connection()

def query(sql, params=None, fetch=True):
    conn = get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params or [])
        if fetch:
            return cur.fetchall()
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def init_db():
    """Run schema.sql on first launch if tables don't exist."""
    schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'database', 'schema.sql')
    conn = get_conn()
    try:
        cur = conn.cursor()
        with open(schema_path, 'r') as f:
            statements = f.read().split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--') and not stmt.startswith('DELIMITER'):
                try:
                    cur.execute(stmt)
                except Exception:
                    pass
        conn.commit()
        print("[DB] Schema initialised")
    except Exception as e:
        print(f"[DB] Schema init warning: {e}")
    finally:
        conn.close()
