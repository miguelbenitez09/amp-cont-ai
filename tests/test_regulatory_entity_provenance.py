from src.data.scrapers.ana_hscode_scraper import PanamaTariffDatabase


def test_curated_entities_expose_scoped_institutional_provenance() -> None:
    items = PanamaTariffDatabase.get_tariff_catalog()
    assert items
    for item in items:
        entities = item.get("entidades_reguladoras", [])
        sources = item.get("regulatory_entity_sources", [])
        assert len(sources) == len(entities)
        assert all(source["evidence_scope"] == "institutional_entry_point_only" for source in sources)
        assert all(source["verification_status"] in {"official_homepage_reference", "unmapped_entity"} for source in sources)
