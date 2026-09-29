"""
Domain Pack & Plugin Manager for amp-cont-ai MLOps Framework v1.0.0.
Discovers, validates, and manages domain plugins decoupled from the MLOps Control Plane.

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Mandatory Attribution
"""

import sys
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PLUGINS_DIR = PROJECT_ROOT / "plugins"


class PluginManager:
    """
    Central discovery and lifecycle manager for domain pack plugins.
    Allows amp-cont-ai to operate as a generic MLOps framework while domain packs
    (e.g., PortOps for maritime operations) provide specialized datasets, features, tools, and regulations.
    """

    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or PLUGINS_DIR

    def discover_plugins(self) -> List[Dict[str, Any]]:
        """Scans plugins/ directory and parses all plugin.yaml manifests."""
        plugins = []
        if not self.plugins_dir.exists():
            return plugins

        for p_dir in self.plugins_dir.iterdir():
            if p_dir.is_dir() and not p_dir.name.startswith((".", "__")):
                manifest_path = p_dir / "plugin.yaml"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f) or {}
                        data["plugin_dir"] = str(p_dir)
                        data["is_installed"] = True
                        data["status"] = "ACTIVE"
                        plugins.append(data)
                    except Exception as e:
                        plugins.append({
                            "name": p_dir.name,
                            "plugin_dir": str(p_dir),
                            "is_installed": True,
                            "status": "ERROR",
                            "error": str(e)
                        })
        return plugins

    def get_plugin(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Retrieves metadata and manifest for a specific plugin."""
        for p in self.discover_plugins():
            if p.get("name", "").lower() == plugin_name.lower():
                return p
        return None

    def get_plugin_tools(self, plugin_name: str) -> List[str]:
        """Lists available tool modules within a domain plugin."""
        p_dir = self.plugins_dir / plugin_name / "tools"
        if not p_dir.exists():
            return []
        tools = []
        for f in p_dir.glob("*.py"):
            if not f.name.startswith((".", "__")):
                tools.append(f.stem)
        return sorted(tools)


if __name__ == "__main__":
    pm = PluginManager()
    found = pm.discover_plugins()
    print(f"Discovered {len(found)} plugins:")
    for p in found:
        print(f" - {p.get('name')} v{p.get('version')}: {p.get('description')}")
