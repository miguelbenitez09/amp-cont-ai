"""
Hugging Face Model Hub Catalog Provider — amp-cont-ai
Enables search, inspection, filtering, and importing models from Hugging Face Hub.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import urllib.request
import urllib.parse
import json
from typing import List, Dict, Any, Optional
from ..catalog_normalizer import NormalizedModel, CatalogNormalizer


class HuggingFaceCatalogProvider:
    """Queries Hugging Face API to discover, inspect, and evaluate model metadata."""

    BASE_URL = "https://huggingface.co/api/models"

    def __init__(self, timeout: float = 3.0):
        self.timeout = timeout

    def search_models(
        self,
        query: Optional[str] = None,
        task: Optional[str] = None,
        limit: int = 15,
        sort: str = "downloads"
    ) -> List[NormalizedModel]:
        """Searches Hugging Face Hub with specified filters."""
        params = {"limit": limit, "sort": sort, "direction": -1}
        if query:
            params["search"] = query
        if task:
            params["pipeline_tag"] = task

        url = f"{self.BASE_URL}?{urllib.parse.urlencode(params)}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "amp-cont-ai/1.0"})
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                results = []
                for item in data:
                    model_id = item.get("id") or item.get("modelId", "")
                    pipeline = item.get("pipeline_tag", "text-generation")
                    
                    # Estimate type
                    if pipeline in ("text-generation", "text2text-generation"):
                        m_type = "llm"
                    elif pipeline in ("feature-extraction", "sentence-similarity"):
                        m_type = "embedding"
                    elif pipeline in ("visual-question-answering", "image-text-to-text"):
                        m_type = "vlm"
                    else:
                        m_type = "other"

                    results.append(CatalogNormalizer.normalize_dict({
                        "model_id": model_id,
                        "name": model_id.split("/")[-1],
                        "family": model_id.split("/")[-1].split("-")[0].lower(),
                        "type": m_type,
                        "task": pipeline,
                        "runtime": "runtime-vllm-primary" if m_type == "llm" else "runtime-local-tabular",
                        "status": "STAGED",
                        "source": "huggingface",
                        "access_policy": "AUTHENTICATED",
                        "metrics": {
                            "downloads": item.get("downloads", 0),
                            "likes": item.get("likes", 0)
                        },
                        "capabilities": [pipeline],
                        "description": f"Hugging Face repository: {model_id} (License: {item.get('private', False) and 'Private' or 'Open'})"
                    }, default_source="huggingface"))
                return results
        except Exception:
            # Fallback for offline mode or network errors
            return self._get_offline_defaults(query, task)

    def _get_offline_defaults(self, query: Optional[str] = None, task: Optional[str] = None) -> List[NormalizedModel]:
        """Provides verified Hugging Face curated templates when network is offline."""
        curated = [
            {
                "model_id": "google/gemma-2-2b-it",
                "name": "gemma-2-2b-it",
                "family": "gemma",
                "type": "llm",
                "task": "text-generation",
                "runtime": "runtime-vllm-primary",
                "status": "STAGED",
                "source": "huggingface_curated",
                "access_policy": "AUTHENTICATED",
                "metrics": {"downloads": 1500000, "likes": 4200},
                "capabilities": ["text-generation", "chat", "tool-calling"],
                "description": "Google Gemma 2 2B Instruct model optimized for lightweight inference."
            },
            {
                "model_id": "BAAI/bge-small-en-v1.5",
                "name": "bge-small-en-v1.5",
                "family": "bert",
                "type": "embedding",
                "task": "feature-extraction",
                "runtime": "runtime-local-tabular",
                "status": "APPROVED",
                "source": "huggingface_curated",
                "access_policy": "PUBLIC",
                "metrics": {"downloads": 4800000, "likes": 1800},
                "capabilities": ["embeddings", "dense-retrieval"],
                "description": "BAAI BGE Small multilingual text embedding model (384 dims)."
            },
            {
                "model_id": "meta-llama/Llama-3.2-1B-Instruct",
                "name": "Llama-3.2-1B-Instruct",
                "family": "llama",
                "type": "llm",
                "task": "text-generation",
                "runtime": "runtime-vllm-primary",
                "status": "STAGED",
                "source": "huggingface_curated",
                "access_policy": "AUTHENTICATED",
                "metrics": {"downloads": 3200000, "likes": 5100},
                "capabilities": ["text-generation", "multilingual"],
                "description": "Meta Llama 3.2 1B Instruct compact edge model."
            }
        ]
        return [CatalogNormalizer.normalize_dict(m, default_source="huggingface_curated") for m in curated]
