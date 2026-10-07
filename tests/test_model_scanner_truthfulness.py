from src.models.discovery.model_scanner import ModelDirectoryScanner


def test_model_catalog_does_not_claim_uninstalled_gemma_or_gpu():
    catalog = ModelDirectoryScanner.scan_catalog()
    assert "candidate_catalog" in catalog
    assert "recommended_catalog" not in catalog
    assert all("Gemma4" not in item["name"] for item in catalog["candidate_catalog"])
    assert isinstance(catalog["hardware_context"]["gpu_detected"], str)
    assert any(item["name"].endswith("qwen3/1.7b") for item in catalog["models"])
    assert catalog["has_local_llm"] is True
