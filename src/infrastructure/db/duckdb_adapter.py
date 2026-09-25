"""
DuckDB & SQLite Embedded Analytics Adapter.
High-performance in-process columnar database adapter for OLAP queries,
fast parquet scanning, and offline edge analytics.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import time
import sqlite3
from typing import Any, Dict, List, Optional
import pandas as pd
from src.infrastructure.db.base import BaseDatabaseAdapter

try:
    import duckdb
    HAS_DUCKDB = True
except ImportError:
    HAS_DUCKDB = False


class DuckDBAdapter(BaseDatabaseAdapter):
    """
    In-memory or file-backed DuckDB adapter with seamless fallback to SQLite.
    Optimized for high-speed parquet querying across 140 months of AMP microdata.
    """

    def __init__(self, database_path: str = ":memory:", pool_size: int = 4):
        super().__init__(connection_uri=database_path, pool_size=pool_size)
        self.database_path = database_path
        self._conn = None
        self._engine_type = "duckdb" if HAS_DUCKDB else "sqlite"

    def connect(self) -> bool:
        try:
            if HAS_DUCKDB:
                self._conn = duckdb.connect(database=self.database_path, read_only=False)
                self._engine_type = "duckdb"
            else:
                self._conn = sqlite3.connect(self.database_path, check_same_thread=False)
                self._conn.row_factory = sqlite3.Row
                self._engine_type = "sqlite"
            self._is_connected = True
            return True
        except Exception as e:
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            finally:
                self._conn = None
                self._is_connected = False

    def health_check(self) -> Dict[str, Any]:
        start = time.perf_counter()
        if not self._is_connected or not self._conn:
            return {"status": "unhealthy", "engine": self._engine_type, "latency_ms": -1.0}
        
        try:
            if self._engine_type == "duckdb":
                self._conn.execute("SELECT 1").fetchall()
            else:
                cursor = self._conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchall()
            latency = (time.perf_counter() - start) * 1000.0
            return {
                "status": "healthy",
                "engine": self._engine_type,
                "latency_ms": round(latency, 3),
                "database_path": self.database_path
            }
        except Exception as e:
            return {"status": "error", "message": str(e), "engine": self._engine_type}

    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self._is_connected:
            self.connect()

        if self._engine_type == "duckdb":
            if params:
                result = self._conn.execute(query, params).df()
            else:
                result = self._conn.execute(query).df()
            return result.to_dict(orient="records")
        else:
            cursor = self._conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def insert_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "append") -> int:
        if not self._is_connected:
            self.connect()

        if self._engine_type == "duckdb":
            if if_exists == "replace":
                self._conn.execute(f"DROP TABLE IF EXISTS {table_name}")
            self._conn.register("tmp_df_view", df)
            self._conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM tmp_df_view WHERE 1=0")
            self._conn.execute(f"INSERT INTO {table_name} SELECT * FROM tmp_df_view")
            self._conn.unregister("tmp_df_view")
            return len(df)
        else:
            df.to_sql(table_name, con=self._conn, if_exists=if_exists, index=False)
            return len(df)
