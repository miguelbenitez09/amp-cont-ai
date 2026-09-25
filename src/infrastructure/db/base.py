"""
Base Universal Database Adapter Interface.
Defines contracts for connection lifecycle, transactions, query execution,
and schema migration management across relational, time-series, and NoSQL engines.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


class BaseDatabaseAdapter(ABC):
    """Abstract Base Class for enterprise database storage adapters."""

    def __init__(self, connection_uri: str, pool_size: int = 5):
        self.connection_uri = connection_uri
        self.pool_size = pool_size
        self._is_connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Establishes connection pool to the underlying database."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Gracefully closes all connections in the pool."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Returns diagnostic dictionary with latency and connection status."""
        pass

    @abstractmethod
    def execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Executes a DML/DQL query and returns results as a list of dicts."""
        pass

    @abstractmethod
    def insert_dataframe(self, table_name: str, df: pd.DataFrame, if_exists: str = "append") -> int:
        """Inserts a pandas DataFrame into target table, returning rows inserted."""
        pass

    @property
    def is_connected(self) -> bool:
        return self._is_connected
