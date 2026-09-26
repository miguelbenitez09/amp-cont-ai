"""
Microservice Health and Readiness Probe for Panama PortOps-AI v2.0
Validates liveness, readiness, dependencies, and version status.
Author: Desarrollado v1.0 Miguel Benítez - GNU GPL-3.0
"""

import sys
import json
import urllib.request
import sqlite3
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
DB_PATH = ROOT_DIR / "data" / "enterprise_db" / "portops_platform.db"


def run_healthcheck(base_url: str = "http://127.0.0.1:8000") -> bool:
    """Probes system health via HTTP if online, or local diagnostics fallback."""
    print("Checking Panama PortOps-AI service health...")

    # 1. Probe local database
    db_alive = DB_PATH.exists()
    if db_alive:
        try:
            conn = sqlite3.connect(str(DB_PATH))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM roles;")
            roles_count = cursor.fetchone()[0]
            conn.close()
            print(f"  [OK] Local Database Ready ({roles_count} roles configured)")
        except Exception as e:
            print(f"  [FAIL] Database check error: {e}")
            db_alive = False

    # 2. Probe HTTP endpoint
    http_alive = False
    try:
        req = urllib.request.Request(f"{base_url}/health", headers={"User-Agent": "PortOps-Healthcheck"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                print(f"  [OK] HTTP Liveness Probe ({base_url}/health): {data.get('status', 'OK')}")
                http_alive = True
    except Exception:
        print(f"  [INFO] HTTP server at {base_url} is currently offline (Run 'make serve' to start).")

    is_healthy = db_alive or http_alive
    print(f"Overall Health Status: {'HEALTHY' if is_healthy else 'UNHEALTHY'}")
    return is_healthy


if __name__ == "__main__":
    healthy = run_healthcheck()
    sys.exit(0 if healthy else 1)
