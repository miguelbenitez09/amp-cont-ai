"""
Tests for Panama National Lakehouse, 17 Ministries Scraper, and Government ISO Compliance.

Validates:
- Comprehensive scraper of 17 Panamanian Ministries (MICI, MEF, MOP, MIAMBIENTE, etc.)
- Detailed ACP canal vessel categories (Neopanamax, Panamax, Bulk, Tanker, LNG, Ro-Ro) and Country Flags
- Climate (IMHPA, ENSO, Cold Fronts, Hurricanes), Festive Overtime Calendar, and Sociopolitical Blockades
- FastApi Serving Endpoints: /api/lakehouse/catalog, /api/lakehouse/query, and /api/governance/iso-compliance

Author: Desarrollado v1.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import pytest
from fastapi.testclient import TestClient
from src.serving.api import app
from src.data.scrapers.panama_ministries_scraper import PanamaMinistriesScraper
from src.data.lakehouse.panama_national_lakehouse import PanamaNationalLakehouse


client = TestClient(app)


class TestPanamaMinistriesScraper:
    def test_scraper_catalog_contains_17_ministries(self):
        scraper = PanamaMinistriesScraper()
        catalog = scraper.get_catalog()
        assert len(catalog) == 17, f"Expected 17 ministries, got {len(catalog)}"

        codes = {m["acronym"] for m in catalog}
        expected_sample = {"MICI", "MEF", "MOP", "MIAMBIENTE", "MIDA", "MINSA", "MITRADEL"}
        assert expected_sample.issubset(codes)

        for item in catalog:
            assert "official_name" in item
            assert "relevance_to_portops" in item
            assert "key_metrics_extracted" in item
            assert len(item["key_metrics_extracted"]) > 0

    def test_scraper_time_series_generation(self):
        scraper = PanamaMinistriesScraper()
        df = scraper.fetch_synthetic_empirical_series()
        assert not df.empty
        assert len(df) >= 130
        assert "period" in df.columns
        assert "mef_pib_crecimiento_trimestral_pct" in df.columns
        assert "mici_zlc_movimiento_usd_millones" in df.columns
        assert "mida_exportacion_banano_cajas" in df.columns
        assert "mitradel_dias_paro_logistico" in df.columns


class TestPanamaNationalLakehouse:
    def test_canal_traffic_detailed_series(self):
        lakehouse = PanamaNationalLakehouse()
        df = lakehouse.generate_acp_detailed_transit_series()
        assert not df.empty
        assert len(df) >= 130
        # Vessel segments
        assert "neopanamax_container_transits" in df.columns
        assert "panamax_container_transits" in df.columns
        assert "bulk_carriers_transits" in df.columns
        assert "lng_lpg_carriers_transits" in df.columns
        assert "vehicle_carriers_roro_transits" in df.columns
        assert "tankers_chemical_transits" in df.columns
        # Country shares
        assert "us_trade_share_pct" in df.columns
        assert "china_trade_share_pct" in df.columns
        assert "japan_trade_share_pct" in df.columns
        assert "chile_trade_share_pct" in df.columns
        # Draft and daily booking caps
        assert "daily_transit_cap" in df.columns
        assert "total_monthly_transits" in df.columns

        # Verify logical value bounds
        assert (df["us_trade_share_pct"] > 60.0).all()
        assert (df["china_trade_share_pct"] > 15.0).all()

    def test_climate_festivities_disruptions(self):
        lakehouse = PanamaNationalLakehouse()
        df = lakehouse.generate_climate_and_disruptions_series()
        assert not df.empty
        assert "enso_oni_sst_anomaly_celsius" in df.columns
        assert "cold_front_crane_shutdown_hours" in df.columns
        assert "hurricane_indirect_impact" in df.columns
        assert "national_holidays_count" in df.columns
        assert "stevedoring_overtime_surcharge_active" in df.columns
        assert "blockade_severity_score" in df.columns
        assert "disruption_event_name" in df.columns

        # Check for July 2022 national strike
        strike_2022 = df[df["period"] == "2022-07"]
        assert not strike_2022.empty
        assert strike_2022.iloc[0]["blockade_severity_score"] >= 0.70
        assert "Julio 2022" in strike_2022.iloc[0]["disruption_event_name"]

        # Check for Oct-Nov 2023 mining blockades
        mining_2023 = df[df["period"] == "2023-11"]
        assert not mining_2023.empty
        assert mining_2023.iloc[0]["blockade_severity_score"] >= 0.90


class TestLakehouseAndGovernanceApiEndpoints:
    def test_get_lakehouse_catalog(self):
        response = client.get("/api/lakehouse/catalog")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "total_ministries_integrated" in data
        assert data["total_ministries_integrated"] == 17
        assert "additional_strategic_sources" in data
        assert "acp_panama_canal" in data["additional_strategic_sources"]
        assert "imhpa_climate" in data["additional_strategic_sources"]

    def test_query_lakehouse_ministries(self):
        payload = {
            "table_name": "panama_17_ministries_indicators",
            "limit": 12
        }
        response = client.post("/api/lakehouse/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["table"] == "panama_17_ministries_indicators"
        assert data["row_count"] == 12
        assert len(data["records"]) == 12
        first = data["records"][0]
        assert "period" in first
        assert "mef_pib_crecimiento_trimestral_pct" in first

    def test_query_lakehouse_acp_transits(self):
        payload = {
            "table_name": "acp_transits_detailed",
            "limit": 6
        }
        response = client.post("/api/lakehouse/query", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["table"] == "acp_transits_detailed"
        assert data["row_count"] == 6

    def test_query_lakehouse_invalid_table(self):
        payload = {
            "table_name": "non_existent_table",
            "limit": 10
        }
        response = client.post("/api/lakehouse/query", json=payload)
        assert response.status_code == 400
        assert "Table non_existent_table not found" in response.json()["detail"]

    def test_get_iso_compliance(self):
        response = client.get("/api/governance/iso-compliance")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "compliant"
        assert "iso_standards" in data
        iso_names = {s["iso"] for s in data["iso_standards"]}
        assert {"ISO/IEC 27001:2022", "ISO/IEC 42001:2023", "ISO/IEC 27701:2019", "ISO 22301:2019"}.issubset(iso_names)
        assert data["panama_government_readiness"]["panama_legal_framework"]["data_protection"] == "Ley 81 de 2019"
        assert "Desarrollado v1.0 Miguel Benítez" in data["signature"]
