"""
Comprehensive Deep UI Inspection and Interaction Verification
Panama PortOps-AI / AMP-CONT-AI
Author: Ing. Miguel Antonio Benítez González (UTP)
"""

import os
import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://127.0.0.1:8000"
AUDIT_DIR = Path("docs/assets/audit/manual_tests")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def deep_inspect_ui():
    console_logs = []
    page_errors = []
    http_errors = []
    test_results = {}

    print(f"=== INICIANDO AUDITORÍA MANUAL EXHAUSTIVA DE LA INTERFAZ: {BASE_URL} ===")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # 1440x900 viewport
        page = browser.new_page(viewport={"width": 1440, "height": 900}, locale="es-PA")

        page.on("console", lambda msg: console_logs.append({
            "type": msg.type,
            "text": msg.text,
            "url": page.url
        }))
        page.on("pageerror", lambda err: page_errors.append(str(err)))
        page.on("response", lambda res: http_errors.append({
            "url": res.url,
            "status": res.status,
            "status_text": res.status_text
        }) if res.status >= 400 else None)

        # -------------------------------------------------------------
        # TEST 1: Carga Inicial de la Página y Encabezado
        # -------------------------------------------------------------
        print("\n[TEST 1] Cargando http://127.0.0.1:8000/...")
        page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)

        page.screenshot(path=str(AUDIT_DIR / "01_landing_page.png"), full_page=False)
        test_results["test_1_title"] = page.title()
        test_results["test_1_heading"] = page.locator("header h1").inner_text() if page.locator("header h1").count() > 0 else "None"
        print(f" -> Título: {test_results['test_1_title']}")
        print(f" -> Encabezado: {test_results['test_1_heading']}")

        # -------------------------------------------------------------
        # TEST 2: Selector de Idiomas (ES / EN / PT)
        # -------------------------------------------------------------
        print("\n[TEST 2] Verificando selector de idiomas i18n...")
        lang_selector = page.locator("#nav-lang-select")
        if lang_selector.count() > 0:
            lang_results = {}
            for lang in ["en", "pt", "es"]:
                lang_selector.select_option(lang)
                time.sleep(0.6)
                badge_text = page.locator("[data-i18n='landing.evidence_badge']").inner_text() if page.locator("[data-i18n='landing.evidence_badge']").count() > 0 else page.locator("body").inner_text()[:40]
                lang_results[lang] = {
                    "lang_attr": page.locator("html").get_attribute("lang"),
                    "badge_sample": badge_text
                }
            test_results["test_2_i18n"] = lang_results
            print(f" -> i18n probado: {lang_results}")
        else:
            test_results["test_2_i18n"] = "Selector #nav-lang-select no encontrado"

        # -------------------------------------------------------------
        # TEST 3: Selector de Temas (Dark / Light / High Contrast)
        # -------------------------------------------------------------
        print("\n[TEST 3] Verificando selector de temas visuales...")
        theme_selector = page.locator("#theme-selector")
        if theme_selector.count() > 0:
            theme_results = {}
            for t in ["theme-cyber-ocean", "theme-radar-amber", "theme-canal-emerald", "theme-tactical-mono", "theme-pacific-sunset", "theme-midnight-cobalt"]:
                try:
                    theme_selector.select_option(t)
                    time.sleep(0.3)
                    theme_results[t] = page.locator("html").get_attribute("data-theme") or page.locator("body").get_attribute("class")
                except Exception as ex:
                    theme_results[t] = str(ex)
            test_results["test_3_themes"] = theme_results
            print(f" -> Temas probados: {theme_results}")
            theme_selector.select_option("theme-cyber-ocean")
        else:
            test_results["test_3_themes"] = "Selector #theme-selector no encontrado"

        # -------------------------------------------------------------
        # TEST 4: Pestañas Principales de Navegación
        # -------------------------------------------------------------
        print("\n[TEST 4] Navegando entre pestañas operacionales...")
        nav_tabs = [
            ("tab-landing", "Inicio & Visión General"),
            ("tab-cot-swarm", "Razonamiento CoT & Agentes"),
            ("tab-customs-lakehouse", "Aduana & RAG"),
            ("tab-forecast", "Pronóstico & What-If"),
            ("tab-benchmark", "Comparativa Multi-Algoritmo"),
            ("tab-diagnostics", "Diagnóstico Estadístico"),
            ("tab-simulation", "Simulación Monte Carlo"),
            ("tab-methodology", "Metodología"),
            ("tab-data-platform", "Data Platform & Calidad"),
            ("tab-security-iam", "Seguridad, IAM & WORM")
        ]
        tabs_visited = {}
        for tab_name_attr, tab_label in nav_tabs:
            loc = page.locator(f"button[data-tab='{tab_name_attr}']")
            if loc.count() > 0:
                loc.click()
                time.sleep(0.7)
                page.screenshot(path=str(AUDIT_DIR / f"04_tab_{tab_name_attr}.png"), full_page=False)
                tabs_visited[tab_label] = "OK"
            else:
                tabs_visited[tab_label] = "NO_ENCONTRADO"
        test_results["test_4_tabs"] = tabs_visited
        print(f" -> Pestañas navegadas: {tabs_visited}")

        # -------------------------------------------------------------
        # TEST 5: Módulo de Aduana & RAG - Búsqueda de Aranceles y Calculadora
        # -------------------------------------------------------------
        print("\n[TEST 5] Probando módulo de Aduana & SIECA...")
        page.locator("button[data-tab='tab-customs-lakehouse']").click()
        time.sleep(0.5)

        # 5.1 Búsqueda arancelaria
        tariff_input = page.locator("#customs-search-input")
        btn_search = page.locator("#btn-customs-search")
        if tariff_input.count() > 0 and btn_search.count() > 0:
            tariff_input.fill("carne")
            btn_search.click()
            time.sleep(1.2)
            results_count = page.locator("#customs-search-results .tariff-item, #customs-search-results div").count()
            test_results["test_5_tariff_search"] = f"{results_count} elementos encontrados para 'carne'"
            print(f" -> Búsqueda 'carne': {results_count} resultados")

        # 5.2 Calculadora de liquidación
        hs_code_input = page.locator("#calc-hs-code")
        cif_input = page.locator("#calc-cif-usd")
        btn_calc = page.locator("#btn-calc-customs")
        if hs_code_input.count() > 0 and cif_input.count() > 0 and btn_calc.count() > 0:
            btn_calc.click()
            time.sleep(0.5)
            val_empty = page.locator("#customs-calc-results").inner_text()

            hs_code_input.fill("0201.30.00.00.20")
            cif_input.fill("25000")
            btn_calc.click()
            time.sleep(1.2)
            page.screenshot(path=str(AUDIT_DIR / "05_customs_calc.png"), full_page=False)
            val_filled = page.locator("#customs-calc-results").inner_text()
            test_results["test_5_calculator"] = {
                "validation_empty": val_empty[:60].replace("\n", " "),
                "result_filled": val_filled[:100].replace("\n", " ")
            }
            print(f" -> Calculadora aduanal: {test_results['test_5_calculator']}")

        # 5.3 Validador ISO 6346
        container_input = page.locator("#container-id-input")
        btn_val_container = page.locator("#btn-validate-container")
        if container_input.count() > 0 and btn_val_container.count() > 0:
            container_input.fill("MSKU1234565")
            btn_val_container.click()
            time.sleep(0.8)
            res_valid = page.locator("#container-validation-results").inner_text()

            container_input.fill("MSKU1234569")
            btn_val_container.click()
            time.sleep(0.8)
            res_invalid = page.locator("#container-validation-results").inner_text()

            test_results["test_5_container_iso"] = {
                "valid_check": "VÁLIDO" in res_valid.upper() or "CORRECTO" in res_valid.upper() or "MSK" in res_valid,
                "invalid_check": "INVÁLIDO" in res_invalid.upper() or "MISMATCH" in res_invalid.upper() or "ERROR" in res_invalid.upper() or "DISCREPANCIA" in res_invalid.upper()
            }
            print(f" -> Validador ISO 6346: {test_results['test_5_container_iso']}")

        # -------------------------------------------------------------
        # TEST 6: Inferencia de Modelos TEUs (Champion Suite)
        # -------------------------------------------------------------
        print("\n[TEST 6] Probando módulo de Pronósticos TEUs...")
        page.locator("button[data-tab='tab-forecast']").click()
        time.sleep(0.5)

        port_select = page.locator("#port-select")
        algo_select = page.locator("#algo-select")
        btn_predict = page.locator("#btn-predict")

        if port_select.count() > 0 and btn_predict.count() > 0:
            port_select.select_option("Puerto Balboa")
            if algo_select.count() > 0:
                algo_select.select_option(index=0)
            btn_predict.click()
            time.sleep(2.0)
            page.screenshot(path=str(AUDIT_DIR / "06_forecast_result.png"), full_page=False)
            res_val = page.locator("#kpi-p50, .kpi-value").first.inner_text() if page.locator("#kpi-p50, .kpi-value").count() > 0 else "N/A"
            test_results["test_6_forecast"] = {
                "executed": True,
                "p50_value": res_val
            }
            print(f" -> Inferencia TEUs: {test_results['test_6_forecast']}")

        # -------------------------------------------------------------
        # TEST 7: Simulación Estocástica Monte Carlo
        # -------------------------------------------------------------
        print("\n[TEST 7] Probando simulación Monte Carlo...")
        page.locator("button[data-tab='tab-simulation']").click()
        time.sleep(0.5)

        btn_sim = page.locator("#btn-simulate")
        if btn_sim.count() > 0:
            btn_sim.click()
            time.sleep(2.0)
            page.screenshot(path=str(AUDIT_DIR / "07_simulation_result.png"), full_page=False)
            var_res = page.locator("#sim-kpi-var95, .kpi-value").first.inner_text() if page.locator("#sim-kpi-var95, .kpi-value").count() > 0 else "N/A"
            test_results["test_7_simulation"] = {
                "executed": True,
                "var95": var_res
            }
            print(f" -> Simulación Monte Carlo: {test_results['test_7_simulation']}")

        # -------------------------------------------------------------
        # TEST 8: Enjambre de Agentes MCP & Razonamiento CoT
        # -------------------------------------------------------------
        print("\n[TEST 8] Probando módulo de Razonamiento CoT & Agentes...")
        page.locator("button[data-tab='tab-cot-swarm']").click()
        time.sleep(0.5)

        btn_run_cot = page.locator("#btn-run-cot")
        if btn_run_cot.count() > 0:
            btn_run_cot.click()
            time.sleep(3.0)
            page.screenshot(path=str(AUDIT_DIR / "08_cot_reasoning.png"), full_page=False)
            cot_text = page.locator("#cot-final-response-box").first.inner_text() if page.locator("#cot-final-response-box").count() > 0 else "N/A"
            test_results["test_8_cot_swarm"] = {
                "executed": True,
                "verdict_snippet": cot_text[:80].replace("\n", " ")
            }
            print(f" -> Razonamiento CoT: {test_results['test_8_cot_swarm']}")

        # -------------------------------------------------------------
        # TEST 9: Calidad de Datos (5D Quality Gates)
        # -------------------------------------------------------------
        print("\n[TEST 9] Probando Quality Gates 5D...")
        page.locator("button[data-tab='tab-data-platform']").click()
        time.sleep(0.5)

        btn_quality = page.locator("#btn-run-quality-gates")
        if btn_quality.count() > 0:
            btn_quality.click()
            time.sleep(1.5)
            page.screenshot(path=str(AUDIT_DIR / "09_quality_gates.png"), full_page=False)
            gate_score = page.locator("#dp-quality-score").inner_text() if page.locator("#dp-quality-score").count() > 0 else "N/A"
            test_results["test_9_quality_gates"] = {
                "executed": True,
                "overall_score": gate_score
            }
            print(f" -> Quality Gates: {test_results['test_9_quality_gates']}")

        # -------------------------------------------------------------
        # TEST 10: Modal de Autenticación, Presets IAM y Login
        # -------------------------------------------------------------
        print("\n[TEST 10] Probando Modal de Iniciar Sesión / IAM...")
        btn_open_login = page.locator("#btn-auth-iam")
        if btn_open_login.count() > 0:
            btn_open_login.click()
            time.sleep(0.8)
            page.screenshot(path=str(AUDIT_DIR / "10_login_modal.png"), full_page=False)

            user_field = page.locator("#auth-input-username")
            pass_field = page.locator("#auth-input-password")
            btn_submit = page.locator("#btn-submit-login")

            test_results["test_10_login_modal_fields"] = {
                "user_field_exists": user_field.count() > 0,
                "pass_field_exists": pass_field.count() > 0,
                "submit_btn_exists": btn_submit.count() > 0
            }

            # Aplicar preset de root
            page.evaluate("() => window.applyAuthPreset && window.applyAuthPreset('root')")
            time.sleep(0.5)
            user_val = user_field.input_value()
            print(f" -> Preset aplicado: usuario '{user_val}'")

            # Ejecutar login
            btn_submit.click()
            time.sleep(1.8)
            page.screenshot(path=str(AUDIT_DIR / "10_logged_in_state.png"), full_page=False)

            hud_role = page.locator("#hud-active-role").inner_text()
            login_status = page.locator("#auth-login-status").inner_text()
            test_results["test_10_login_execution"] = {
                "hud_role": hud_role,
                "status_text": login_status
            }
            print(f" -> Resultado de autenticación: {test_results['test_10_login_execution']}")

            # Cerrar modal
            page.evaluate("() => window.closeAuthModal && window.closeAuthModal()")
            time.sleep(0.5)

        browser.close()

    print("\n==================== RESUMEN DE ERRORES DETECTADOS ====================")
    print(f"Errores no controlados de página (Page Errors): {len(page_errors)}")
    for pe in page_errors:
        print(f"  [ERROR GRAVE] {pe}")

    print(f"\nRespuestas HTTP 4xx/5xx: {len(http_errors)}")
    for he in http_errors:
        print(f"  [HTTP {he['status']}] {he['url']} ({he['status_text']})")

    console_warnings = [c for c in console_logs if c["type"] in ["warning", "error"]]
    print(f"\nMensajes de Consola (Warnings/Errors): {len(console_warnings)}")
    for cw in console_warnings[:10]:
        print(f"  [{cw['type'].upper()}] {cw['text']}")

    report = {
        "tests": test_results,
        "page_errors": page_errors,
        "http_errors": http_errors,
        "console_warnings": console_warnings
    }
    Path("logs/audit_runs/manual_deep_ui_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Reporte exportado a logs/audit_runs/manual_deep_ui_audit.json")

if __name__ == "__main__":
    deep_inspect_ui()
