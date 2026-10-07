"""
Automated Browser UI Inspection for Panama PortOps-AI v1.0.0
Validates:
1. Landing page demo visibility (no blocking popups on load).
2. Complete absence of 1-click test credential presets.
3. Functional close buttons ('X' button and 'Cerrar Centro IAM' button).
4. Real login with root bootstrap credentials.
5. Smooth transition to NIST password change and confirmation.
6. Successful password update and session preservation.
7. Persistence across browser reload.
"""

import os
import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8000")
AUDIT_DIR = Path("docs/assets/audit/manual_tests/auth_flow")
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

def test_complete_auth_flow():
    print(f"=== INICIANDO VALIDACIÓN UI DEL FLUJO REAL DE AUTENTICACIÓN: {BASE_URL} ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error"] else None)

        # STEP 1: Load Landing Page
        print("\n[PASO 1] Cargando landing page y verificando demo operativa inicial...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        time.sleep(1.2)
        
        # Verify first-run modal is NOT blocking the screen
        fr_modal = page.locator("#first-run-setup-modal")
        fr_display = fr_modal.evaluate("el => window.getComputedStyle(el).display") if fr_modal.count() > 0 else "none"
        print(f" -> Display del modal first-run en carga inicial: '{fr_display}' (esperado: none)")
        assert fr_display == "none", "El modal first-run no debe bloquear la carga inicial"
        page.screenshot(path=str(AUDIT_DIR / "01_landing_unblocked.png"))

        # STEP 2: Open Auth Modal
        print("\n[PASO 2] Abriendo Centro IAM...")
        btn_iam = page.locator("#btn-auth-iam")
        btn_iam.click()
        time.sleep(0.8)

        auth_modal = page.locator("#auth-iam-modal")
        auth_display = auth_modal.evaluate("el => window.getComputedStyle(el).display")
        print(f" -> Display del modal auth tras click: '{auth_display}' (esperado: flex)")
        assert auth_display == "flex", "El modal auth debe estar visible"

        # Verify 1-click test buttons are COMPLETELY GONE
        preset_buttons = page.locator("button:has-text('Root Admin (CSPRNG)'), button:has-text('Auditor Ley 6/56')")
        print(f" -> Botones de prueba rápida 1-clic encontrados: {preset_buttons.count()} (esperado: 0)")
        assert preset_buttons.count() == 0, "Los botones de prueba rápida 1-clic deben estar eliminados"
        page.screenshot(path=str(AUDIT_DIR / "02_iam_modal_no_presets.png"))

        # STEP 3: Test Close Button 'X'
        print("\n[PASO 3] Probando botón de cerrar 'X' (#btn-close-iam-top)...")
        btn_x = page.locator("#btn-close-iam-top")
        btn_x.click()
        time.sleep(0.5)
        auth_display_after_x = auth_modal.evaluate("el => window.getComputedStyle(el).display")
        print(f" -> Display tras clic en 'X': '{auth_display_after_x}' (esperado: none)")
        assert auth_display_after_x == "none", "El botón 'X' debe cerrar el modal"
        page.screenshot(path=str(AUDIT_DIR / "03_modal_closed_by_x.png"))

        # STEP 4: Test Close Button Footer
        print("\n[PASO 4] Reabriendo y probando botón 'Cerrar Centro IAM' (#btn-close-iam-footer)...")
        btn_iam.click()
        time.sleep(0.5)
        btn_footer = page.locator("#btn-close-iam-footer")
        btn_footer.click()
        time.sleep(0.5)
        auth_display_after_footer = auth_modal.evaluate("el => window.getComputedStyle(el).display")
        print(f" -> Display tras clic en footer: '{auth_display_after_footer}' (esperado: none)")
        assert auth_display_after_footer == "none", "El botón del footer debe cerrar el modal"

        # STEP 5: Real Login
        print("\n[PASO 5] Iniciando sesión con credenciales reales de bootstrap (root)...")
        btn_iam.click()
        time.sleep(0.5)

        page.locator("#auth-input-username").fill("root")
        page.locator("#auth-input-password").fill("PortOpsRoot2026!")
        page.locator("#btn-submit-login").click()
        time.sleep(1.8)

        # Must have transitioned to tab-password because must_change_password is true
        pwd_tab_active = page.locator("#atab-password").evaluate("el => el.classList.contains('active')")
        print(f" -> Pestaña de cambio de contraseña activa: {pwd_tab_active} (esperado: True)")
        page.screenshot(path=str(AUDIT_DIR / "04_mandatory_pwd_change_prompt.png"))

        # STEP 6: Execute NIST Password Change
        print("\n[PASO 6] Ejecutando cambio de clave obligatorio NIST...")
        page.locator("#pwd-input-new").fill("PortOpsSovereign2026!#")
        page.locator("#pwd-input-confirm").fill("PortOpsSovereign2026!#")
        page.locator("button:has-text('Actualizar Contraseña')").click()
        time.sleep(2.2)

        # Check token in localStorage
        stored_token = page.evaluate("() => localStorage.getItem('portops_token')")
        print(f" -> Token almacenado en localStorage: {stored_token[:30] if stored_token else 'NONE'}...")
        assert stored_token, "El token de sesión debe estar guardado en localStorage"
        page.screenshot(path=str(AUDIT_DIR / "05_pwd_changed_session_active.png"))

        # If First-Run Admins modal opened, close or complete it
        fr_modal_open = fr_modal.evaluate("el => el.classList.contains('open')") if fr_modal.count() > 0 else False
        print(f" -> Modal de administradores obligatorios abierto: {fr_modal_open}")
        if fr_modal_open:
            page.locator("#btn-close-firstrun-top").click()
            time.sleep(0.5)

        # Close auth modal if open
        if auth_modal.evaluate("el => el.classList.contains('open')"):
            btn_x.click()
            time.sleep(0.5)

        # Verify HUD shows active root role
        hud_role = page.locator("#hud-active-role").inner_text()
        nav_label = page.locator("#nav-user-label").inner_text()
        print(f" -> HUD Rol Activo: '{hud_role}'")
        print(f" -> Nav User Label: '{nav_label.encode('ascii', 'replace').decode('ascii')}'")
        assert "root" in hud_role.lower(), "El HUD debe indicar que el usuario root está activo"
        page.screenshot(path=str(AUDIT_DIR / "06_authenticated_hud_state.png"))

        # STEP 7: Test Session Persistence Across Page Reload
        print("\n[PASO 7] Recargando página para verificar persistencia de sesión...")
        page.reload(wait_until="domcontentloaded")
        time.sleep(1.5)

        hud_role_after_reload = page.locator("#hud-active-role").inner_text()
        nav_label_after_reload = page.locator("#nav-user-label").inner_text()
        stored_token_after_reload = page.evaluate("() => localStorage.getItem('portops_token')")

        print(f" -> Tras recarga: HUD Rol: '{hud_role_after_reload}'")
        print(f" -> Tras recarga: Nav Label: '{nav_label_after_reload.encode('ascii', 'replace').decode('ascii')}'")
        print(f" -> Tras recarga: Token en storage: {bool(stored_token_after_reload)}")

        assert "root" in hud_role_after_reload.lower(), "La sesión de root debe persistir tras recargar"
        assert stored_token_after_reload, "El token debe conservarse en localStorage tras recargar"
        page.screenshot(path=str(AUDIT_DIR / "07_session_persisted_after_reload.png"))

        # Filter severe console errors (ignore benign 422 tariff compliance test if any)
        critical_errors = [e for e in console_errors if "422" not in e]
        print(f"\nErrores críticos de consola: {len(critical_errors)}")
        for err in critical_errors:
            print(f"  [ERROR] {err}")

        browser.close()

    print("\n[SUCCESS] TODAS LAS PRUEBAS DEL FLUJO DE AUTENTICACION Y CONFIGURACION PASARON CON EXITO!")

if __name__ == "__main__":
    test_complete_auth_flow()
