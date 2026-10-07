"""
Local Model Scanner & Catalog Engine for Panama PortOps-AI v1.0.0
Scans designated model directories, Ollama local cache, and local paths
to produce a live catalog of available AI models, quantizations, and weights.

Author: Desarrollado v1.0.0 Miguel Benítez (UTP)
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import os
import glob
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import requests

from src.infrastructure.secrets.manager import SecretManager
from src.infrastructure.hardware.profiler import HardwareProfiler

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class ModelDirectoryScanner:
    """Scans and indexes local AI models, weights, and runtimes."""

    SUPPORTED_EXTENSIONS = [".gguf", ".safetensors", ".bin", ".joblib", ".pt", ".onnx"]

    @classmethod
    def get_search_paths(cls) -> List[Path]:
        """Resolves active and custom search paths for local models."""
        paths = []
        # 1. Project models directory
        proj_models = PROJECT_ROOT / "models"
        paths.append(proj_models)

        # 2. Configured custom path from SecretManager or ENV
        custom_path = SecretManager.get_secret("MODELS_DIRECTORY_PATH", "")
        if custom_path and os.path.exists(custom_path):
            paths.append(Path(custom_path))

        # 3. User local cache if on Windows
        user_home = Path.home()
        ollama_models = user_home / ".ollama" / "models"
        if ollama_models.exists():
            paths.append(ollama_models)

        hf_cache = user_home / ".cache" / "huggingface" / "hub"
        if hf_cache.exists():
            paths.append(hf_cache)

        return list(dict.fromkeys(paths))

    @classmethod
    def scan_catalog(cls) -> Dict[str, Any]:
        """
        Scans all designated directories and returns catalog of models,
        quantizations, and readiness status.
        """
        models_found: List[Dict[str, Any]] = []
        paths_scanned: List[str] = []
        total_size_bytes = 0

        # Retrieve host hardware for sizing recommendation
        gpu_info = HardwareProfiler.inspect_nvidia_gpu()
        mem_info = HardwareProfiler.inspect_memory()
        vram_mb = gpu_info.get("total_vram_mib", 4096) or 4096
        ram_gb = mem_info.get("total_gb", 16.0) or 16.0

        for p in cls.get_search_paths():
            paths_scanned.append(str(p))
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
                continue

            for ext in cls.SUPPORTED_EXTENSIONS:
                for file_path in p.rglob(f"*{ext}"):
                    if file_path.is_file():
                        size_bytes = file_path.stat().st_size
                        total_size_bytes += size_bytes
                        size_mb = round(size_bytes / (1024 * 1024), 2)

                        # Determine format and quantization
                        fname = file_path.name.lower()
                        quant = "FP32 / Native"
                        if "q4" in fname or "4bit" in fname:
                            quant = "4-bit (Q4_K_M / AWQ)"
                        elif "q8" in fname or "8bit" in fname:
                            quant = "8-bit (Q8_0)"
                        elif "q5" in fname:
                            quant = "5-bit (Q5_K_M)"
                        elif "fp16" in fname:
                            quant = "FP16 (Half Precision)"

                        model_type = "LLM / Transformer"
                        if ext == ".joblib":
                            model_type = "Tabular Quantile Ensemble (LightGBM/RF)"
                        elif "gemma" in fname:
                            model_type = "Gemma4 Distilled (Aduanas & HS Codes)"
                        elif "llama" in fname:
                            model_type = "Llama 3.3 Maritime Reasoning"

                        models_found.append({
                            "name": file_path.stem,
                            "filename": file_path.name,
                            "path": str(file_path),
                            "format": ext.lstrip(".").upper(),
                            "size_mb": size_mb,
                            "size_human": f"{size_mb:.1f} MB" if size_mb < 1024 else f"{size_mb/1024:.2f} GB",
                            "quantization": quant,
                            "model_type": model_type,
                            "modified_at": datetime.fromtimestamp(file_path.stat().st_mtime, timezone.utc).isoformat(),
                            "vram_compatible": (size_mb * 1.25) <= vram_mb
                        })

        # Ollama stores weights as extensionless content-addressed blobs, so
        # filesystem extension scanning alone misses valid installed models.
        ollama_root = Path.home() / ".ollama" / "models"
        manifest_root = ollama_root / "manifests"
        if manifest_root.exists():
            for manifest in manifest_root.rglob("*"):
                if not manifest.is_file():
                    continue
                try:
                    payload = json.loads(manifest.read_text(encoding="utf-8"))
                    digest = next((layer.get("digest", "") for layer in payload.get("layers", [])
                                   if layer.get("mediaType", "").endswith(".model")), "")
                    size = next((int(layer.get("size", 0)) for layer in payload.get("layers", [])
                                 if layer.get("digest") == digest), 0)
                    rel = manifest.relative_to(manifest_root).as_posix()
                    if digest and not any(m.get("digest") == digest for m in models_found):
                        models_found.append({"name": rel, "filename": manifest.name,
                            "path": str(manifest), "format": "OLLAMA", "size_mb": round(size / 1048576, 2),
                            "size_human": f"{size / 1073741824:.2f} GB", "quantization": "Ollama managed",
                            "model_type": "LLM / Transformer", "digest": digest,
                            "modified_at": datetime.fromtimestamp(manifest.stat().st_mtime, timezone.utc).isoformat(),
                            "vram_compatible": (size / 1048576 * 1.25) <= vram_mb})
                except (OSError, ValueError, json.JSONDecodeError, StopIteration):
                    continue

        # Ollama manifests are valid local LLM evidence even though their
        # content-addressed blobs have no model-file extension.
        has_llm = any(m["format"] in ["GGUF", "SAFETENSORS", "BIN", "OLLAMA"] for m in models_found)
        total_storage_mb = sum(float(m.get("size_mb", 0)) for m in models_found)

        # Keep candidates separate from installed artifacts. A name in a
        # recommendation catalog is never evidence that weights exist locally.
        return {
            "author": "Desarrollado v1.0.0 Miguel Benítez (UTP)",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "paths_scanned": paths_scanned,
            "total_models_detected": len(models_found),
            "total_storage_mb": round(total_size_bytes / (1024 * 1024), 2),
            "has_local_llm": has_llm,
            "hardware_context": {
                "gpu_detected": gpu_info.get("device_name") or gpu_info.get("name") or "NOT_DETECTED",
                "vram_available_mb": vram_mb,
                "ram_total_gb": ram_gb,
                "recommended_quantization": "AWQ 4-bit / GGUF Q4_K_M (Máx. 3.2 GB en VRAM)"
            },
            "models": models_found,
            "candidate_catalog": [
                {
                    "id": "qwen2.5-3b-instruct",
                    "name": "Qwen2.5 3B Instruct",
                    "description": "Candidato abierto para consultas con RAG; debe descargarse, verificarse y evaluarse antes de activarlo.",
                    "size_estimated": "2-3 GB cuantizado",
                    "quantization": "GGUF Q4_K_M / AWQ",
                    "status": "CANDIDATE_ONLY"
                },
                {
                    "id": "lightgbm-quantile-champion",
                    "name": "LightGBM Quantile Ensemble (P10/P50/P90)",
                    "description": "Modelo campeón para predicción de demanda de TEUs a 1-6 meses con garantía anti-cruce.",
                    "size_estimated": "18.2 MB",
                    "quantization": "FP32 Vectorizado",
                    "status": "INSTALLED_ONLY_IF_FOUND_IN_MODELS"
                },
                {
                    "id": "qwen2.5-7b-instruct",
                    "name": "Qwen2.5 7B Instruct",
                    "description": "Candidato para análisis documental complejo si la memoria disponible lo permite; requiere benchmark reproducible.",
                    "size_estimated": "5-6 GB cuantizado",
                    "quantization": "GGUF Q4_K_M / AWQ",
                    "status": "CANDIDATE_ONLY"
                }
            ]
        }
