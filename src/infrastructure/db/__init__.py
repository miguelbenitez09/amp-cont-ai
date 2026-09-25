"""
Infrastructure Database Adapters Package.
Author: Desarrollado v1.0 Miguel Benítez
"""

from src.infrastructure.db.base import BaseDatabaseAdapter
from src.infrastructure.db.duckdb_adapter import DuckDBAdapter
from src.infrastructure.db.postgres_adapter import PostgresTimescaleAdapter
from src.infrastructure.db.redis_adapter import RedisCacheAdapter
from src.infrastructure.db.factory import DatabaseFactory

__all__ = [
    "BaseDatabaseAdapter",
    "DuckDBAdapter",
    "PostgresTimescaleAdapter",
    "RedisCacheAdapter",
    "DatabaseFactory"
]
