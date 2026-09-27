"""
Runtime Probe Base Interface — amp-cont-ai
Standard interface for probing inference engines and runtime instances.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseRuntimeProbe(ABC):
    """Abstract base class for all runtime probes."""

    @abstractmethod
    def probe(self) -> Dict[str, Any]:
        """Executes probe and returns standardized status dictionary."""
        pass

    @abstractmethod
    def list_served_models(self) -> List[str]:
        """Returns list of served model IDs."""
        pass
