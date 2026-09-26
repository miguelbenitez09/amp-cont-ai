"""
Configuration and Authorization Seeder CLI for Panama PortOps-AI v2.0
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db"

# Add project root to sys.path
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from db.seeds.seed_data import seed_database


def run_seeder(db_path: Path = DB_PATH) -> bool:
    """Executes database seeding for roles, permissions, and authoritative sources."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        print(f"Seeding configuration into {db_path.name}...")
        seed_database(conn)
        print("Seeding completed successfully.")
        conn.close()
        return True
    except Exception as e:
        print(f"Seeding failed: {e}")
        conn.close()
        return False


if __name__ == "__main__":
    success = run_seeder()
    sys.exit(0 if success else 1)
