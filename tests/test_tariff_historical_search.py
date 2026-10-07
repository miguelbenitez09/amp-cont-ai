from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase


def test_historical_catalog_finds_pencil_and_eraser_terms():
    pencils = PanamaTariffDatabase.search_by_text("lápiz")
    erasers = PanamaTariffDatabase.search_by_text("borrador")
    assert pencils
    assert erasers
    assert any("9609" in item["hs_code_panama"] for item in pencils)
    assert any("401692" in item["hs_code_panama"] or "392610" in item["hs_code_panama"] for item in erasers)


def test_multi_token_query_and_no_controlado_false_positive():
    beef = PanamaTariffDatabase.search_by_text("carne bovina")
    assert {item["hs_code_6"] for item in beef} >= {"020110", "020130"}
    controlled = PanamaTariffDatabase.search_by_text("controlado")
    assert all(item.get("tipo_mercancia") == "MATERIAL_CONTROLADO" for item in controlled)


def test_unknown_historical_code_cannot_be_liquidated_with_fallback_rate():
    try:
        PanamaTariffDatabase.calculate_landed_customs_cost("960910100000", 1000)
    except ValueError as exc:
        assert "regla ANA vigente" in str(exc)
    else:
        raise AssertionError("Historical observation must not receive a fabricated tax rate")
