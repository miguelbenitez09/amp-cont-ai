"""
Manual UI Automated Exploration & Defect Discovery Script
Panama PortOps-AI / AMP-CONT-AI UI Audit
Author: Ing. Miguel Antonio Benítez González (UTP)
"""

import sys
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:8000"

def test_ui():
    console_messages = []
    page_errors = []
    failed_requests = []
    http_errors = []

    print(f"[AUDIT] Starting Playwright UI inspection at: {BASE_URL}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="es-PA"
        )
        page = context.new_page()

        # Listen to events
        page.on("console", lambda msg: console_messages.append({"type": msg.type, "text": msg.text, "location": msg.location}))
        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("requestfailed", lambda req: failed_requests.append({"url": req.url, "failure": req.failure}))
        def handle_response(res):
            if res.status >= 400:
                http_errors.append({"url": res.url, "status": res.status, "status_text": res.status_text})
        page.on("response", handle_response)

        # 1. Navigate to root
        print(f"[AUDIT] Navigating to {BASE_URL}/...")
        page.goto(f"{BASE_URL}/", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)

        # Title and URL
        title = page.title()
        current_url = page.url
        print(f"[AUDIT] Page title: '{title}' | URL: {current_url}")

        # Check DOM text for critical cues
        body_text = page.locator("body").inner_text()
        has_undefined = "undefined" in body_text.lower()
        has_null = "null" in body_text.lower()
        print(f"[AUDIT] Body text length: {len(body_text)} | has 'undefined': {has_undefined} | has 'null': {has_null}")

        # Screenshot landing / initial state
        Path("docs/assets/audit").mkdir(parents=True, exist_ok=True)
        page.screenshot(path="docs/assets/audit/initial_state.png", full_page=True)
        print("[AUDIT] Saved docs/assets/audit/initial_state.png")

        # 2. Inspect Navigation / Tabs
        tabs = page.locator("nav button, nav a, .tab-btn, [role='tab'], .nav-link, button.nav-btn").all()
        print(f"[AUDIT] Found {len(tabs)} navigation/tab elements.")

        tab_results = []
        for i, tab in enumerate(tabs[:15]): # inspect top tabs
            try:
                t_text = tab.inner_text().strip()
                t_id = tab.get_attribute("id") or ""
                tab.click(timeout=3000)
                time.sleep(0.5)
                tab_results.append({"index": i, "id": t_id, "text": t_text, "status": "clicked"})
            except Exception as e:
                tab_results.append({"index": i, "id": t_id, "text": t_text, "error": str(e)})

        # 3. Check for Broken Images
        images = page.locator("img").all()
        broken_images = []
        for img in images:
            src = img.get_attribute("src") or ""
            try:
                is_natural = img.evaluate("el => el.naturalWidth > 0")
                if not is_natural:
                    broken_images.append(src)
            except Exception:
                pass
        print(f"[AUDIT] Broken images found: {len(broken_images)} -> {broken_images}")

        # 4. Check Language switcher if present
        lang_select = page.locator("#nav-lang-select, select.lang-selector, #language-select")
        lang_switch_worked = False
        if lang_select.count() > 0:
            print("[AUDIT] Found language selector, testing language changes...")
            for l in ["en", "pt", "es"]:
                try:
                    lang_select.first.select_option(l)
                    time.sleep(0.5)
                    lang_switch_worked = True
                except Exception as e:
                    print(f"[WARN] Language switch to {l} failed: {e}")

        # 5. Check forms or action buttons (e.g., login, calculate, simulate, evaluate)
        buttons = page.locator("button:visible").all()
        print(f"[AUDIT] Total visible buttons: {len(buttons)}")

        # 6. Specific interactive probes: Customs tariff calculator, container validation, model inference
        interactive_errors = []

        # Customs tariff
        btn_calc = page.locator("#btn-calc-customs, button:has-text('Calcular'), button:has-text('Tariff')")
        if btn_calc.count() > 0:
            print("[AUDIT] Testing customs tariff calculator...")
            try:
                btn_calc.first.click(timeout=3000)
                time.sleep(1)
            except Exception as e:
                interactive_errors.append(f"Customs calc button click error: {e}")

        # Container validator
        btn_container = page.locator("#btn-validate-container, button:has-text('Validar Contenedor'), button:has-text('ISO 6346')")
        if btn_container.count() > 0:
            print("[AUDIT] Testing container validator button...")
            try:
                btn_container.first.click(timeout=3000)
                time.sleep(1)
            except Exception as e:
                interactive_errors.append(f"Container validate button error: {e}")

        # Simulation
        btn_sim = page.locator("#btn-run-simulation, button:has-text('Simular'), button:has-text('Monte Carlo')")
        if btn_sim.count() > 0:
            print("[AUDIT] Testing simulation button...")
            try:
                btn_sim.first.click(timeout=3000)
                time.sleep(1)
            except Exception as e:
                interactive_errors.append(f"Simulation button error: {e}")

        page.screenshot(path="docs/assets/audit/interacted_state.png", full_page=True)

        browser.close()

    print("\n==================== AUDIT REPORT SUMMARY ====================")
    print(f"Page Title: {title}")
    print(f"Total Console Messages: {len(console_messages)}")
    console_errors = [m for m in console_messages if m["type"] in ["error", "warning"]]
    print(f"Console Errors/Warnings ({len(console_errors)}):")
    for ce in console_errors:
        print(f"  [{ce['type'].upper()}] {ce['text']} (at {ce.get('location', '')})")

    print(f"\nUncaught Page Exceptions ({len(page_errors)}):")
    for pe in page_errors:
        print(f"  [PAGE ERROR] {pe}")

    print(f"\nFailed Network Requests ({len(failed_requests)}):")
    for fr in failed_requests:
        print(f"  [NET FAIL] {fr['url']}: {fr['failure']}")

    print(f"\nHTTP 4xx/5xx Responses ({len(http_errors)}):")
    for he in http_errors:
        print(f"  [HTTP {he['status']}] {he['url']} ({he['status_text']})")

    print(f"\nBroken Images: {broken_images}")
    print(f"Interactive Errors: {interactive_errors}")
    print("==============================================================")

    audit_summary = {
        "title": title,
        "console_errors": console_errors,
        "page_errors": page_errors,
        "failed_requests": failed_requests,
        "http_errors": http_errors,
        "broken_images": broken_images,
        "interactive_errors": interactive_errors
    }
    Path("logs/audit_runs").mkdir(parents=True, exist_ok=True)
    Path("logs/audit_runs/ui_audit_summary.json").write_text(json.dumps(audit_summary, indent=2, ensure_ascii=False), encoding="utf-8")

if __name__ == "__main__":
    test_ui()
