"""
scripts/add_user.py
-------------------
Add a user to the BiscuitAI system (run from project root).

Usage:
    python scripts/add_user.py
    python scripts/add_user.py --email ops@factory.com --name "Ravi Kumar" --role operator
"""
import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from backend.utils.db import query, init_db


def add_user(email: str, name: str, role: str = "operator") -> dict:
    email = email.strip().lower()
    name  = name.strip()

    if not email or "@" not in email:
        raise ValueError("Invalid email address")
    if not name:
        raise ValueError("Name cannot be empty")
    if role not in ("admin", "operator"):
        raise ValueError("Role must be 'admin' or 'operator'")

    existing = query("SELECT id FROM users WHERE email=%s", [email])
    if existing:
        print(f"[WARNING] User with email '{email}' already exists (id={existing[0]['id']})")
        return existing[0]

    uid = query(
        "INSERT INTO users (email, name, role, is_active) VALUES (%s, %s, %s, 1)",
        [email, name, role],
        fetch=False,
    )
    print(f"[OK] User created — id={uid}, email={email}, name={name}, role={role}")
    return {"id": uid, "email": email, "name": name, "role": role}


def interactive():
    print("\n  BiscuitAI — Add User")
    print("  " + "─" * 36)
    email = input("  Email   : ").strip()
    name  = input("  Name    : ").strip()
    role  = input("  Role (operator/admin) [operator]: ").strip() or "operator"
    print()
    try:
        user = add_user(email, name, role)
        print(f"\n  ✓ Done. User id={user['id']}")
        print(f"  They can now sign in at the login page using OTP sent to {email}.\n")
    except Exception as e:
        print(f"  [ERROR] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a BiscuitAI user")
    parser.add_argument("--email", help="User email")
    parser.add_argument("--name",  help="User full name")
    parser.add_argument("--role",  default="operator", choices=["admin","operator"])
    args = parser.parse_args()

    try:
        init_db()
    except Exception as e:
        print(f"[DB] {e}")

    if args.email and args.name:
        try:
            add_user(args.email, args.name, args.role)
        except Exception as e:
            print(f"[ERROR] {e}")
            sys.exit(1)
    else:
        interactive()
