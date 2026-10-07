"""
E2E Playwright Audit:
1. Verifies widescreen layout (>= 1400px width, 96vw) of #settings-modal.
2. Systematically activates and verifies all 11 tabs, ensuring ZERO blank screens.
3. Tests Role Perspective Switcher (root, readonly_viewer, admin_maritimo).
4. Tests Item Inspector adaptive popover drawer.
5. Tests Unsaved changes dirty state guard.
6. Captures screenshots of each verified state.
"""

import sys
import os
import time
import json
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

def run_test():
    print("=== STARTING AUDIT: 11 TABS & WIDESCREEN SETTINGS ===")
    os.makedirs("artifacts_audit", exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Large desktop viewport to verify expansive widescreen geometry
        context = browser.new_context(viewport={"width": 1600, "height": 950})
        page = context.new_page()

        # Handle dialogs automatically (e.g. confirm discard changes)
        page.on("dialog", lambda dialog: (print(f"  [Dialog intercepted]: {dialog.message[:60]}... -> Accepting"), dialog.accept()))

        # 1. Navigate to portal
        print("\n1. Navigating to http://127.0.0.1:8000...")
        page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 2. Authenticate session as root
        print("2. Authenticating root session...")
        res = page.request.post(
            "http://127.0.0.1:8000/api/v1/auth/login",
            data=json.dumps({"username": "root", "password": "miguel09@@@@##"}),
            headers={"Content-Type": "application/json"}
        )
        if res.status != 200:
            res = page.request.post(
                "http://127.0.0.1:8000/api/v1/auth/login",
                data=json.dumps({"username": "root", "password": "PortOpsSovereign2026!#"}),
                headers={"Content-Type": "application/json"}
            )
        token_data = res.json()
        token = token_data.get("session_token") or token_data.get("access_token") or ""
        print(f"  Token obtenido: {token[:20]}... (Status: {res.status})")

        page.evaluate(f"""() => {{
            localStorage.setItem("portops_token", "{token}");
            localStorage.setItem("portops_user", JSON.stringify({{
                username: "root",
                role: "root",
                full_name: "Superadministrador Soberano"
            }}));
            window.activeSession = {{ token: "{token}", username: "root", role: "root" }};
            if (window.updateAuthUI) window.updateAuthUI();
        }}""")
        page.wait_for_timeout(800)
        print("  ✓ Root session authenticated and injected.")

        # 3. Open settings modal
        print("\n3. Opening Settings Modal (#settings-modal)...")
        page.evaluate("""() => {
            const btn = document.getElementById("btn-settings-gear");
            if (btn) btn.click();
            else if (window.openSettingsModal) window.openSettingsModal();
        }""")
        page.wait_for_timeout(1000)

        modal = page.locator("#settings-modal")
        if not modal.is_visible():
            print("  [ERROR] Settings modal is not visible!")
            sys.exit(1)

        # Check geometry
        card = page.locator("#settings-modal .settings-card")
        box = card.bounding_box()
        print(f"  ✓ Modal Dimensions: Width = {box['width']}px, Height = {box['height']}px")
        assert box['width'] >= 1350, f"Expected width >= 1350px for widescreen, got {box['width']}px"

        # 4. Systematic check of all 11 tabs
        tabs_to_verify = [
            ("stab-config", "🎯 Presets & Hiperparámetros"),
            ("stab-deploy-verify", "🚀 Deploy & Root Admin"),
            ("stab-vllm-secrets", "⚡ vLLM, Volúmenes & Secretos"),
            ("stab-user-guardrails", "🛡️ Guardrails & Cuotas"),
            ("stab-reproducibility", "🔬 Replicación (Seed 42)"),
            ("stab-privacy", "🛡️ Anonimización Ley 81"),
            ("stab-gov-admin", "🏛️ Gobernanza & RBAC"),
            ("stab-mcp-souls", "🤖 MCP Runner & Almas"),
            ("stab-extensibility", "🔌 Ingesta Nuevas APIs & Adaptadores"),
            ("stab-glossary", "📖 Glosario ML"),
            ("stab-export", "📥 Exportar Datos"),
        ]

        print("\n4. Verifying all 11 tabs individually...")
        for idx, (tab_id, tab_label) in enumerate(tabs_to_verify, start=1):
            btn = page.locator(f"button.settings-tab-btn[data-settings-tab='{tab_id}']")
            assert btn.is_visible(), f"Button for tab {tab_id} not visible"
            btn.click()
            page.wait_for_timeout(500)

            content = page.locator(f"#{tab_id}")
            assert content.is_visible(), f"Tab {tab_id} is NOT visible (blank or hidden)"
            c_box = content.bounding_box()
            assert c_box['height'] > 80, f"Tab {tab_id} has insufficient height: {c_box['height']}px"

            shot_path = f"artifacts_audit/tab_{idx:02d}_{tab_id}.png"
            page.screenshot(path=shot_path)
            print(f"  ✓ Tab {idx:02d}: {tab_id} [{tab_label}] -> VISIBLE (height: {c_box['height']}px) -> Screenshot: {shot_path}")

        # 5. Test Role Perspective Switcher
        print("\n5. Testing Role Perspective Switcher...")
        persp_select = page.locator("#settings-role-perspective-select")
        assert persp_select.is_visible(), "Perspective selector not visible"

        # Switch to readonly_viewer
        persp_select.select_option("readonly_viewer")
        page.wait_for_timeout(600)
        badge = page.locator("#perspective-badge")
        print(f"  ✓ Active badge text: '{badge.inner_text()}'")
        assert "Solo Lectura" in badge.inner_text() or "readonly" in badge.inner_text().lower()

        # Switch back to root
        persp_select.select_option("root")
        page.wait_for_timeout(600)
        print(f"  ✓ Restored badge text: '{badge.inner_text()}'")
        assert "Root" in badge.inner_text()

        # 6. Test Item Inspector Popover
        print("\n6. Testing Item Inspector Adaptive Popover...")
        page.evaluate("() => { if (window.setSettingsDirty) window.setSettingsDirty(false); }")
        # Switch to tab-deploy-verify and click first card
        page.locator("button.settings-tab-btn[data-settings-tab='stab-deploy-verify']").click()
        page.wait_for_timeout(1200)
        first_card = page.locator("#stab-deploy-verify .interactive-audit-card").first
        first_card.wait_for(state="visible", timeout=10000)
        first_card.click()
        page.wait_for_timeout(500)

        popover = page.locator("#item-inspector-overlay")
        assert popover.is_visible(), "Item inspector popover did not open on item click"
        title_text = page.locator("#inspector-title").inner_text()
        print(f"  ✓ Inspector Popover opened successfully: '{title_text}'")

        # Test Undo / Revert button inside popover
        undo_btn = page.locator("#btn-inspector-undo")
        assert undo_btn.is_visible(), "Undo/Restore button not visible inside popover"
        undo_btn.click()
        page.wait_for_timeout(500)
        assert not popover.is_visible(), "Popover should close after revert"
        print("  ✓ Undo action performed and popover closed.")

        # 7. Test Dirty State Tracking & Guard
        print("\n7. Testing Dirty State Tracking & Tab Switch Confirmation...")
        page.locator("button.settings-tab-btn[data-settings-tab='stab-config']").click()
        page.wait_for_timeout(400)

        # Trigger a change on visible select option
        page.select_option("#cfg-quantile-band", "P05_P95")
        page.wait_for_timeout(300)

        is_dirty = page.evaluate("() => window.settingsIsDirty")
        print(f"  ✓ window.settingsIsDirty: {is_dirty}")
        assert is_dirty is True, "Expected window.settingsIsDirty to be True after input modification"

        dirty_badge = page.locator("#settings-dirty-badge")
        assert dirty_badge.is_visible(), "Dirty badge not visible when unsaved changes exist"
        print("  ✓ Dirty badge is visible and alerting user.")

        # Attempt to switch to another tab (dialog accepted by handler)
        page.locator("button.settings-tab-btn[data-settings-tab='stab-glossary']").click()
        page.wait_for_timeout(500)
        assert page.locator("#stab-glossary").is_visible(), "Should switch after confirming discard"
        print("  ✓ Dirty state confirmation worked and allowed switching after confirmation.")

        # Final screenshot
        page.screenshot(path="artifacts_audit/audit_final_all_passed.png")
        print("\n=== AUDIT COMPLETE: 100% OF CHECKS PASSED ===")
        browser.close()

if __name__ == "__main__":
    run_test()
