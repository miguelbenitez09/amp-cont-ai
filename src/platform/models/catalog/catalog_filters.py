"""
Catalog Filters — amp-cont-ai
Provides composable filtering for model lists across multiple dimensions.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

from typing import List, Optional
from .catalog_normalizer import NormalizedModel


class CatalogFilter:
    """Filters model lists based on criteria."""

    @staticmethod
    def apply(
        models: List[NormalizedModel],
        query: Optional[str] = None,
        family: Optional[str] = None,
        model_type: Optional[str] = None,
        runtime: Optional[str] = None,
        task: Optional[str] = None,
        status: Optional[str] = None,
        access_policy: Optional[str] = None,
        only_champion: bool = False
    ) -> List[NormalizedModel]:
        filtered = models

        if only_champion:
            filtered = [m for m in filtered if m.is_champion]

        if query:
            q = query.lower()
            filtered = [
                m for m in filtered
                if q in m.model_id.lower() or q in m.name.lower() or (m.description and q in m.description.lower())
            ]

        if family:
            f_lower = family.lower()
            filtered = [m for m in filtered if m.family.lower() == f_lower]

        if model_type:
            t_lower = model_type.lower()
            filtered = [m for m in filtered if m.type.lower() == t_lower]

        if runtime:
            r_lower = runtime.lower()
            filtered = [m for m in filtered if r_lower in m.runtime.lower()]

        if task:
            task_lower = task.lower()
            filtered = [m for m in filtered if task_lower in m.task.lower()]

        if status:
            s_upper = status.upper()
            filtered = [m for m in filtered if m.status.upper() == s_upper]

        if access_policy:
            p_upper = access_policy.upper()
            filtered = [m for m in filtered if m.access_policy.upper() == p_upper]

        return filtered
