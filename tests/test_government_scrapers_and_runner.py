"""
Unit & Integration Tests for Government Scrapers and Autonomous Validation Runner.
Verifies:
1. AMP Statistics Scraper (1997-2025P multi-terminal container throughput & bunkering)
2. Panama Macroeconomics, Energy Tariffs & Multimodal Cargo Scraper
3. Autonomous Loop Engineering Validation Runner

Author: Desarrollado v1.0.0 Miguel Benítez
License: GNU GPL-3.0 with Section 7 Mandatory Attribution
"""

import pytest
from pathlib import Path
import pandas as pd
from src.data.scrapers.amp_statistics_scraper import AMPStatisticsScraper
from src.data.scrapers.macroeconomic_scraper import MacroeconomicScraper
from scripts.autonomous_validation_runner import AutonomousValidationRunner


class TestAMPStatisticsScraper:
    def test_amp_raw_discovery(self):
        scraper = AMPStatisticsScraper()
        raw_files = scraper.discover_raw_amp_files()
        assert len(raw_files) > 0
        assert all("sha256" in f for f in raw_files)

    def test_amp_container_series(self):
        scraper = AMPStatisticsScraper()
        df = scraper.build_container_movements_time_series(start_year=2020, end_year=2024)
        assert not df.empty
        assert "teu_total" in df.columns
        assert "terminal_code" in df.columns
        assert "transshipment_share_pct" in df.columns
        assert (df["transshipment_share_pct"] >= 80.0).all()
        # Verify all major terminals are present
        terminals = set(df["terminal_code"].unique())
        assert {"BALBOA", "CRISTOBAL", "MIT", "PSA", "CCT"}.issubset(terminals)

    def test_amp_bunkering_series(self):
        scraper = AMPStatisticsScraper()
        df = scraper.build_bunkering_statistics_time_series(start_year=2020, end_year=2024)
        assert not df.empty
        assert "total_bunker_sales_mt" in df.columns
        assert "vlsfo_sales_mt" in df.columns
        # Post-2020 VLSFO dominates high sulfur fuel oil
        assert (df["vlsfo_sales_mt"] > df["ifo380_sales_mt"]).all()

    def test_amp_silver_manifest_integrity(self):
        scraper = AMPStatisticsScraper()
        manifest = scraper.export_silver_lakehouse()
        assert "tables" in manifest
        assert "container_movements_silver" in manifest["tables"]
        assert "amp_bunkering_silver" in manifest["tables"]
        assert manifest["author"] == "Desarrollado v1.0.0 Miguel Benítez"


class TestMacroeconomicScraper:
    def test_macro_energy_multimodal_series(self):
        scraper = MacroeconomicScraper()
        df = scraper.build_macro_energy_multimodal_series(start_year=2020, end_year=2024)
        assert not df.empty
        assert "mef_pib_crecimiento_anual_pct" in df.columns
        assert "asep_tarifa_electrica_puerto_usd_kwh" in df.columns
        assert "vlsfo_bunker_panama_usd_mt" in df.columns
        assert "acp_total_monthly_transits" in df.columns
        assert "tocumen_air_cargo_tons" in df.columns
        assert "pcrc_railway_interoceanic_teu" in df.columns

    def test_macro_silver_export(self):
        scraper = MacroeconomicScraper()
        manifest = scraper.export_silver_dataset()
        assert manifest["records"] > 0
        assert Path(manifest["file_path"]).exists()
        assert len(manifest["sha256"]) == 64


class TestAutonomousValidationRunner:
    def test_autonomous_runner_execution(self):
        runner = AutonomousValidationRunner()
        passed = runner.run_all()
        assert passed is True
        assert runner.diagnostics["status"] == "PASSED"
        assert runner.diagnostics["checks"]["mlops_catalogs"]["passed"] is True
        assert runner.diagnostics["checks"]["domain_plugins"]["passed"] is True
        assert runner.diagnostics["checks"]["database"]["passed"] is True
        assert runner.diagnostics["checks"]["medallion_lakehouse"]["passed"] is True
        assert runner.diagnostics["checks"]["scrapers_and_landing"]["passed"] is True
