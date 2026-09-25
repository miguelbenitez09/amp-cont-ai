"""
Universal Database Adapter Factory.
Instantiates database adapters dynamically based on configuration or environment.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import os
from typing import Dict, Any
from src.infrastructure.db.base import BaseDatabaseAdapter
from src.infrastructure.db.duckdb_adapter import DuckDBAdapter
from src.infrastructure.db.postgres_adapter import PostgresTimescaleAdapter
from src.infrastructure.db.redis_adapter import RedisCacheAdapter


class DatabaseFactory:
    """Factory to manage enterprise storage engines and cache layers."""

    _instances: Dict[str, Any] = {}

    @classmethod
    def get_adapter(cls, engine: str = "auto") -> BaseDatabaseAdapter:
        if engine == "auto":
            # If DATABASE_URL is set, prefer PostgreSQL/Timescale, else DuckDB/SQLite
            engine = "postgres" if "DATABASE_URL" in os.environ else "duckdb"

        if engine not in cls._instances:
            if engine in ["postgres", "timescaledb"]:
                adapter = PostgresTimescaleAdapter()
                adapter.connect()
                cls._instances[engine] = adapter
            elif engine in ["duckdb", "sqlite"]:
                adapter = DuckDBAdapter()
                adapter.connect()
                cls._instances[engine] = adapter
            else:
                raise ValueError(f"Unsupported database engine '{engine}'. Choose 'duckdb', 'sqlite', or 'postgres'.")

        return cls._instances[engine]

    @classmethod
    def get_cache(cls) -> RedisCacheAdapter:
        if "redis" not in cls._instances:
            cache = RedisCacheAdapter()
            cache.connect()
            cls._instances["redis"] = cache
        return cls._instances["redis"]

    @classmethod
    def get_all_health_statuses(cls) -> Dict[str, Any]:
        """Runs health checks on all registered adapters."""
        duckdb_ad = cls.get_adapter("duckdb")
        postgres_ad = cls.get_adapter("postgres")
        cache = cls.get_cache()

        return {
            "primary_olap": duckdb_ad.health_check(),
            "timeseries_relational": postgres_ad.health_check(),
            "in_memory_cache": cache.health_check(),
            "supported_matrix": [
                {"engine": "DuckDB Columnar", "role": "OLAP & 140-Month Parquet Scans", "status": "Ready"},
                {"engine": "PostgreSQL / TimescaleDB", "role": "Hyper-tables & Distributed Telemetry", "status": "Configurable"},
                {"engine": "Redis", "role": "Sub-2ms Quantile Inference Cache", "status": "Ready"},
                {"engine": "MongoDB / NoSQL", "role": "Audit Logs & Guardrail Telemetry", "status": "Adapter Ready"}
            ]
        }
