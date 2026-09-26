"""
Model Promotion CLI for Panama PortOps-AI v2.0
Enforces governance approval workflow: only 'ml_reviewer' or 'root' may promote to Champion.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import sqlite3
import argparse
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.models.registry.manager import ModelLifecycleManager
from src.auth.authorization import AuthorizationEngine

DB_PATH = ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db"


def promote_model_cli(request_id: str, reviewer_username: str, notes: str = "") -> bool:
    """Approves and promotes a model request to production champion."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Find reviewer user_id
    cursor.execute("SELECT user_id FROM users WHERE username = ?;", (reviewer_username,))
    row = cursor.fetchone()
    if not row:
        print(f"Error: Reviewer user '{reviewer_username}' not found.")
        conn.close()
        return False
    reviewer_id = row[0]

    # Get reviewer roles
    roles = AuthorizationEngine.get_user_roles(conn, reviewer_id)
    print(f"Reviewer '{reviewer_username}' roles: {roles}")

    success, message = ModelLifecycleManager.approve_promotion(
        conn=conn,
        request_id=request_id,
        reviewer_id=reviewer_id,
        reviewer_roles=roles,
        notes=notes
    )
    conn.close()

    print(f"Promotion Result: {'SUCCESS' if success else 'FAILED'}")
    print(f"Message: {message}")
    return success


def main():
    parser = argparse.ArgumentParser(description="Panama PortOps-AI Model Promotion CLI")
    parser.add_argument("--request-id", type=str, required=True, help="ID of model approval request")
    parser.add_argument("--reviewer", type=str, required=True, help="Username of ML Reviewer or Root")
    parser.add_argument("--notes", type=str, default="Approved via CLI", help="Reviewer audit notes")
    args = parser.parse_args()

    ok = promote_model_cli(args.request_id, args.reviewer, args.notes)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
