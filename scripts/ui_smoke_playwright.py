"""Responsive, provenance-oriented smoke checks for the operational /app UI.

Run against an already started local server:
    python scripts/ui_smoke_playwright.py --url http://127.0.0.1:8000/app
"""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass

from playwright.sync_api import sync_playwright


@dataclass
class ViewportResult:
    width: int
    height: int
    horizontal_overflow: bool
    languages: dict[str, str]
    calculator_validation: str
    calculator_blocked_message: str
    container_validation: str
    quick_filter_count: int
    has_undefined_text: bool
    operational_badge: str
    translated_titles: dict[str, str]
    auth_dialog_accessible: bool


def run(url: str) -> list[ViewportResult]:
    viewports = [(390, 844), (768, 1024), (1440, 900)]
    results: list[ViewportResult] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        for width, height in viewports:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.goto(url, wait_until="domcontentloaded")
            page.wait_for_timeout(900)
            page.locator("#btn-auth-iam").click()
            auth_dialog_accessible = page.evaluate("""() => {
                const modal = document.querySelector('#auth-iam-modal');
                return modal.getAttribute('role') === 'dialog' && modal.getAttribute('aria-modal') === 'true'
                    && !!modal.getAttribute('aria-labelledby') && modal.contains(document.activeElement);
            }""")
            for _ in range(18):
                page.keyboard.press("Tab")
                auth_dialog_accessible &= page.evaluate("document.querySelector('#auth-iam-modal').contains(document.activeElement)")
            auth_dialog_accessible &= page.locator("#nav-lang-select").get_attribute("aria-label") is not None
            auth_dialog_accessible &= page.locator("#theme-selector").get_attribute("aria-label") is not None
            page.keyboard.press("Escape")
            auth_dialog_accessible &= not page.locator("#auth-iam-modal").is_visible()
            auth_dialog_accessible &= page.evaluate("document.activeElement.id === 'btn-auth-iam'")
            if page.locator("#workspace-navigation-toggle").is_visible():
                page.locator("#workspace-navigation-toggle").click()
            page.locator("#tab-btn-customs").click()
            page.locator("#btn-calc-customs").click()
            calculator_validation = page.locator("#customs-calc-results").inner_text()
            page.locator("#calc-hs-code").fill("2710.19.21.00.00")
            page.locator("#calc-cif-usd").fill("10000")
            page.locator("#btn-calc-customs").click()
            page.wait_for_timeout(1200)
            calculator_blocked_message = page.locator("#customs-calc-results").inner_text()
            page.locator("#btn-validate-container").click()
            container_validation = page.locator("#container-validation-results").inner_text()
            languages = {}
            translated_titles = {}
            for lang in ("es", "en", "pt"):
                page.locator("#nav-lang-select").select_option(lang)
                languages[lang] = page.locator("html").get_attribute("lang") or ""
                translated_titles[lang] = page.locator("[data-i18n='customs.calc_title']").inner_text()
            body_text = page.locator("body").inner_text()
            results.append(ViewportResult(
                width=width,
                height=height,
                horizontal_overflow=page.evaluate("document.documentElement.scrollWidth > window.innerWidth"),
                languages=languages,
                calculator_validation=calculator_validation.strip(),
                calculator_blocked_message=calculator_blocked_message.strip(),
                container_validation=container_validation.strip(),
                quick_filter_count=page.locator("#customs-quick-filters button").count(),
                has_undefined_text="undefined" in body_text.lower(),
                operational_badge=page.locator("#health-badge").inner_text(),
                translated_titles=translated_titles,
                auth_dialog_accessible=auth_dialog_accessible,
            ))
            page.close()
        browser.close()
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:8000/app")
    args = parser.parse_args()
    results = run(args.url)
    failures = []
    for result in results:
        if result.horizontal_overflow:
            failures.append(f"{result.width}: horizontal overflow")
        if result.languages != {"es": "es", "en": "en", "pt": "pt"}:
            failures.append(f"{result.width}: i18n language selector")
        if "Completa un código HS" not in result.calculator_validation:
            failures.append(f"{result.width}: calculator did not reject empty input")
        if "Liquidación bloqueada" not in result.calculator_blocked_message or "Siguiente paso" not in result.calculator_blocked_message:
            failures.append(f"{result.width}: candidate-rule explanation missing")
        if "Identificador" not in result.container_validation and "11" not in result.container_validation:
            failures.append(f"{result.width}: container did not reject empty input")
        if result.quick_filter_count < 8:
            failures.append(f"{result.width}: quick filters incomplete")
        if result.has_undefined_text:
            failures.append(f"{result.width}: visible undefined value")
        if len(set(result.translated_titles.values())) != 3:
            failures.append(f"{result.width}: customs title was not translated per language")
        if not result.auth_dialog_accessible:
            failures.append(f"{result.width}: auth dialog semantics or focus")
    print(json.dumps({"viewports": [asdict(result) for result in results], "passed": not failures, "failures": failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
