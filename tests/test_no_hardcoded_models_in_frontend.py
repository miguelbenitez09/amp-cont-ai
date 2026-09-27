"""
Contract Test: Zero Hardcoded Models in Frontend — amp-cont-ai
Verifies Section 3 and Section 56 of Plan Maestro:
Guarantees that index.html and app.js do not hardcode model options in HTML selects.
Author: Desarrollado v1.0.0 Miguel Benítez - GNU GPL-3.0
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_index_html_has_no_hardcoded_algorithm_options():
    """Asserts that <select id='algo-select'> and <select id='api-ctrl-algo'> do not contain hardcoded option lists."""
    html_path = PROJECT_ROOT / "src" / "serving" / "static" / "index.html"
    assert html_path.exists()
    content = html_path.read_text(encoding="utf-8")

    # Match algo-select inner content
    algo_match = re.search(r'<select\s+id=[\'"]algo-select[\'"][^>]*>(.*?)</select>', content, re.DOTALL)
    assert algo_match is not None, "algo-select element not found in index.html"
    inner_html = algo_match.group(1).strip()

    # Must NOT have multiple hardcoded options
    option_count = len(re.findall(r'<option\s+', inner_html))
    assert option_count <= 1, f"Found {option_count} options in algo-select! Must be populated dynamically from catalog."
    assert "Ensamble Champion (LightGBM Cuantiles P10/P50/P90 - WAPE 9.11%)" not in inner_html

    # Check api-ctrl-algo
    api_match = re.search(r'<select\s+id=[\'"]api-ctrl-algo[\'"][^>]*>(.*?)</select>', content, re.DOTALL)
    assert api_match is not None
    api_options = len(re.findall(r'<option\s+', api_match.group(1)))
    assert api_options <= 1, f"Found {api_options} options in api-ctrl-algo! Must be populated dynamically."


def test_app_js_implements_dynamic_model_catalog_loader():
    """Asserts that app.js defines and bootstraps loadDynamicModelCatalog."""
    js_path = PROJECT_ROOT / "src" / "serving" / "static" / "js" / "app.js"
    assert js_path.exists()
    content = js_path.read_text(encoding="utf-8")

    assert "loadDynamicModelCatalog" in content
    assert "/api/v1/models/catalog" in content
