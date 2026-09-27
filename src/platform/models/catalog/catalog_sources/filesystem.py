"""
Filesystem Model Discovery Source — amp-cont-ai
Scans designated directories for binary weights, joblib models, GGUF and safetensors files.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from ..catalog_normalizer import NormalizedModel, CatalogNormalizer


class FilesystemCatalogSource:
    """Scans local filesystem for serialized models and weights."""

    SUPPORTED_EXTENSIONS = {".joblib", ".pkl", ".gguf", ".safetensors", ".onnx", ".bin"}

    def __init__(self, search_paths: Optional[List[str]] = None):
        self.search_paths = search_paths or ["models", "artifacts"]

    def discover_files(self) -> List[NormalizedModel]:
        """Scans directories and returns normalized model candidates."""
        discovered: List[NormalizedModel] = []

        for base_dir in self.search_paths:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in self.SUPPORTED_EXTENSIONS:
                        full_path = os.path.join(root, f)
                        try:
                            f_size = os.path.getsize(full_path)
                            base_name = os.path.splitext(f)[0]
                            
                            # Determine type and family
                            m_type = "llm" if ext in (".gguf", ".safetensors") else "tabular_regression"
                            runtime = "runtime-vllm-primary" if m_type == "llm" else "runtime-local-tabular"
                            
                            discovered.append(CatalogNormalizer.normalize_dict({
                                "model_id": f"fs-{base_name}",
                                "name": base_name,
                                "version": "1.0.0",
                                "type": m_type,
                                "runtime": runtime,
                                "status": "READY",
                                "source": "filesystem_scan",
                                "artifact_path": full_path,
                                "hardware_requirements": {
                                    "file_size_mb": round(f_size / (1024 * 1024), 2)
                                },
                                "description": f"Discovered on disk: {full_path} ({round(f_size / (1024 * 1024), 2)} MB)"
                            }, default_source="filesystem_scan"))
                        except Exception:
                            continue

        return discovered
