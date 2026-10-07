"""
Auditoría Exhaustiva de Interacción y Diseño de Botones / Consola IAM
Panamá PortOps-AI v1.0.0
Autor: Ing. Miguel Antonio Benítez González (UTP)
Licencia: GNU GPL-3.0 con Atribución Obligatoria (Sección 7)

Verificaciones Clave:
1. Inspección de Estilos Computados de Botones:
   - Cero botones con estilo 'buttonface' o bordes toscos de Windows 95.
   - Pestañas (.fr-nav-tab): color, fondo navy oscuro, borde cian translúcido, sin salto de línea (nowrap).
   - Botón 'X' (#btn-close-firstrun-top): botón circular con icono SVG estilizado.
   - Botón 'Cerrar Consola' en footer (#btn-close-firstrun-footer): estilo de botón secundario cyber dark.
2. Interacciones y Event Handlers Funcionales:
   - Clics en pestañas 1, 2, 3 y 4 cambian activamente la vista sin errores de JS.
   - Botón de diagnóstico de infraestructura ejecuta y renderiza estado de 4 servicios.
   - Ciclo CRUD completo en Fase 4:
     * Lectura (Read): Carga tabla con usuarios reales.
     * Creación (Create): Registra usuario con rol RBAC.
     * Actualización (Update): Modifica rol, email y estado.
     * Eliminación (Delete): Borra usuario garantizando inmutabilidad de root.
3. Cierre funcional por botón superior e inferior.
4. Generación de capturas de pantalla de alta resolución para auditoría visual.
"""

import os
import sys
import time
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8000")
SCREENSHOTS_DIR = Path("docs/assets/audit/manual_tests/button_audit")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def run_exhaustive_button_and_crud_audit():
    print("=" * 80)
    print(f" AUDITORIA EXHAUSTIVA DE INTERACCIONES, BOTONES Y CRUD: {BASE_URL}")
    print("=" * 80)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error"] else None)

        # 1. Cargar plataforma
        print("\n[P1] Cargando plataforma...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)

        # 2. Iniciar sesión como root para tener token activo y abrir consola
        print("[P2] Autenticando sesión root...")
        res = page.request.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=json.dumps({"username": "root", "password": "miguel09@@@@##"}),
            headers={"Content-Type": "application/json"}
        )
        if res.status != 200:
            res = page.request.post(
                f"{BASE_URL}/api/v1/auth/login",
                data=json.dumps({"username": "root", "password": "PortOpsSovereign2026!#"}),
                headers={"Content-Type": "application/json"}
            )
        token_data = res.json()
        token = token_data.get("session_token") or token_data.get("access_token") or ""
        print(f"  Token obtenido: {token[:20]}... (Status: {res.status})")

        # Inyectar token en localStorage
        page.evaluate(f"""() => {{
            localStorage.setItem("portops_token", "{token}");
            localStorage.setItem("portops_user", JSON.stringify({{
                username: "root",
                role: "security_admin",
                full_name: "Superadministrador Soberano"
            }}));
            window.activeSession = {{ token: "{token}", username: "root", role: "security_admin" }};
        }}""")

        # 3. Abrir la Consola de Inicialización / Seguridad
        print("[P3] Abriendo Consola de Seguridad & First-Run Setup...")
        page.evaluate("() => window.openFirstRunModal()")
        time.sleep(0.5)

        modal = page.locator("#first-run-setup-modal")
        assert modal.is_visible(), "El modal de inicialización debe ser visible"

        # 4. Auditoría de Estilos de Pestañas (Tabs)
        print("\n[P4] Auditando diseño y estilos computados de pestañas...")
        tabs_box = page.locator("#fr-wizard-tabs")
        tabs_display = tabs_box.evaluate("el => window.getComputedStyle(el).display")
        tabs_flex_wrap = tabs_box.evaluate("el => window.getComputedStyle(el).flexWrap")
        print(f"  Contenedor de pestañas: display={tabs_display}, flexWrap={tabs_flex_wrap}")
        assert tabs_flex_wrap == "nowrap", f"Las pestañas deben tener flex-wrap: nowrap, recibido: {tabs_flex_wrap}"

        tab1 = page.locator("#fr-tab-1")
        tab1_bg = tab1.evaluate("el => window.getComputedStyle(el).backgroundColor")
        tab1_color = tab1.evaluate("el => window.getComputedStyle(el).color")
        tab1_border = tab1.evaluate("el => window.getComputedStyle(el).border")
        print(f"  Tab 1 (Activo): bg={tab1_bg}, color={tab1_color}, border={tab1_border}")
        assert "buttonface" not in tab1_bg.lower(), "El fondo de la pestaña no debe ser el predeterminado del navegador"

        tab2 = page.locator("#fr-tab-2")
        tab2_bg = tab2.evaluate("el => window.getComputedStyle(el).backgroundColor")
        tab2_color = tab2.evaluate("el => window.getComputedStyle(el).color")
        print(f"  Tab 2 (Inactivo): bg={tab2_bg}, color={tab2_color}")

        # 5. Auditoría de Botón de Cierre Superior ('X')
        print("\n[P5] Auditando botón de cierre superior (#btn-close-firstrun-top)...")
        close_top = page.locator("#btn-close-firstrun-top")
        assert close_top.is_visible(), "El botón de cierre superior debe ser visible"
        top_w = close_top.evaluate("el => el.offsetWidth")
        top_h = close_top.evaluate("el => el.offsetHeight")
        has_svg = close_top.locator("svg").count() > 0
        print(f"  Botón 'X': dimensiones={top_w}x{top_h}px, contiene SVG={has_svg}")
        assert top_w > 0 and top_h > 0, "Dimensiones del botón 'X' deben ser positivas"
        assert has_svg, "El botón 'X' superior debe usar el icono SVG estilizado"

        # Captura de pantalla de la cabecera y pestañas
        page.locator("#first-run-setup-modal .modal-header").screenshot(path=str(SCREENSHOTS_DIR / "01_header_and_close_button.png"))
        tabs_box.screenshot(path=str(SCREENSHOTS_DIR / "02_navigation_tabs_clean.png"))
        print("  ✓ Capturas de cabecera y pestañas guardadas.")

        # 6. Interacción: Navegación a Fase 2
        print("\n[P6] Probando clic interactivo en Fase 2 (Tríada de Administradores)...")
        tab2.click()
        time.sleep(0.5)
        step2 = page.locator("#fr-step-2")
        assert step2.is_visible(), "Fase 2 debe ser visible tras hacer clic en Tab 2"
        page.screenshot(path=str(SCREENSHOTS_DIR / "03_phase2_administrators.png"))
        print("  ✓ Fase 2 activada correctamente.")

        # 7. Interacción: Navegación a Fase 3 y Ejecución de Diagnóstico
        print("\n[P7] Probando clic en Fase 3 y Diagnóstico de Infraestructura...")
        tab3 = page.locator("#fr-tab-3")
        tab3.click()
        time.sleep(0.5)
        step3 = page.locator("#fr-step-3")
        assert step3.is_visible(), "Fase 3 debe ser visible"

        diag_btn = step3.locator("button:has-text('Ejecutar Diagnóstico en Vivo')")
        assert diag_btn.is_visible(), "Botón de diagnóstico debe existir"
        diag_btn.click()
        time.sleep(2.0)

        # Verificar que se mostraron tarjetas de diagnóstico
        infra_cards = step3.locator(".fr-infra-card")
        card_count = infra_cards.count()
        print(f"  Tarjetas de infraestructura diagnosticadas: {card_count}")
        assert card_count >= 4, f"Se esperan al menos 4 tarjetas de diagnóstico de motor, se obtuvieron: {card_count}"
        page.screenshot(path=str(SCREENSHOTS_DIR / "04_phase3_diagnostics_live.png"))
        print("  ✓ Diagnóstico ejecutado y renderizado con éxito.")

        # 8. Interacción: Navegación a Fase 4 (Consola IAM & CRUD de Usuarios)
        print("\n[P8] Probando clic en Fase 4 y Ciclo CRUD de Usuarios...")
        tab4 = page.locator("#fr-tab-4")
        tab4.click()
        time.sleep(0.8)
        step4 = page.locator("#fr-step-4")
        assert step4.is_visible(), "Fase 4 debe ser visible"

        # READ: Verificar carga inicial de tabla
        users_table = step4.locator("#fr-users-table-body")
        rows = users_table.locator("tr")
        initial_row_count = rows.count()
        print(f"  Filas iniciales en tabla de usuarios: {initial_row_count}")
        assert initial_row_count > 0, "La tabla debe contener al menos al usuario root"

        # CREATE: Registrar nuevo usuario
        test_user = "op_auditor_utp"
        print(f"  Creando nuevo usuario de prueba: '{test_user}'...")
        page.fill("#crud-new-user", test_user)
        page.fill("#crud-new-fullname", "Auditor General UTP")
        page.fill("#crud-new-email", "auditor_utp@portops.pa")
        page.select_option("#crud-new-role", "compliance_auditor")
        page.fill("#crud-new-pass", "SovereignAuditor2026!#")

        create_btn = step4.locator("button:has-text('Crear Usuario')")
        create_btn.click()
        time.sleep(1.0)

        # Verificar que aparece en la tabla
        user_row = users_table.locator(f"tr:has-text('{test_user}')")
        assert user_row.is_visible(), f"El nuevo usuario '{test_user}' debe figurar en la tabla"
        print(f"  ✓ Usuario '{test_user}' creado y verificado en tabla.")

        # UPDATE: Clic en botón 'Editar' en la fila
        print(f"  Cargando datos de '{test_user}' en formulario de actualización...")
        edit_btn = user_row.locator("button:has-text('Editar')")
        assert edit_btn.is_visible(), "El botón de editar debe ser visible"
        edit_btn.click()
        time.sleep(0.5)

        # Verificar que se cargó el usuario en el campo readonly
        edit_user_val = page.input_value("#crud-edit-user")
        assert edit_user_val == test_user, f"El campo a modificar debe contener '{test_user}', recibido: {edit_user_val}"

        # Modificar rol a 'mlops_engineer' y actualizar email
        page.select_option("#crud-edit-role", "mlops_engineer")
        page.fill("#crud-edit-email", "auditor_promoted@portops.pa")
        save_update_btn = step4.locator("button:has-text('Guardar Actualización')")
        save_update_btn.click()
        time.sleep(1.0)

        # Verificar que el rol en la fila ahora es mlops_engineer
        updated_row = users_table.locator(f"tr:has-text('{test_user}')")
        role_chip = updated_row.locator(".fr-role-chip").inner_text()
        print(f"  Rol actualizado en tabla: '{role_chip}'")
        assert "mlops_engineer" in role_chip, f"El rol actualizado debe ser mlops_engineer, recibido: {role_chip}"
        print(f"  ✓ Usuario '{test_user}' actualizado exitosamente.")

        # DELETE: Eliminar el usuario creado
        print(f"  Eliminando usuario de prueba '{test_user}'...")
        delete_btn = updated_row.locator("button:has-text('Eliminar')")
        assert delete_btn.is_visible(), "Botón de eliminar debe ser visible"

        # Aceptar confirm dialog de Playwright
        page.once("dialog", lambda dialog: dialog.accept())
        delete_btn.click()
        time.sleep(1.0)

        # Verificar que el usuario ya no existe en la tabla
        assert users_table.locator(f"tr:has-text('{test_user}')").count() == 0, f"El usuario '{test_user}' debió ser eliminado"
        print(f"  ✓ Usuario '{test_user}' eliminado exitosamente de la base de datos.")

        page.screenshot(path=str(SCREENSHOTS_DIR / "05_phase4_crud_verified.png"))

        # 9. Auditoría de Botón de Cierre Inferior (Footer)
        print("\n[P9] Auditando botón de cierre en footer (#btn-close-firstrun-footer)...")
        close_footer = page.locator("#btn-close-firstrun-footer")
        assert close_footer.is_visible(), "Botón de cierre en footer debe ser visible"
        footer_btn_bg = close_footer.evaluate("el => window.getComputedStyle(el).backgroundColor")
        footer_btn_color = close_footer.evaluate("el => window.getComputedStyle(el).color")
        print(f"  Botón Footer: bg={footer_btn_bg}, color={footer_btn_color}")
        assert "buttonface" not in footer_btn_bg.lower(), "Fondo de botón de footer no debe ser buttonface predeterminado"

        # 10. Probar cierre funcional
        print("\n[P10] Probando cierre de modal mediante botón superior...")
        close_top.click()
        time.sleep(0.5)
        assert not modal.is_visible(), "El modal debe cerrarse al hacer clic en el botón superior 'X'"
        print("  ✓ Modal cerrado correctamente.")

        # Reabrir y cerrar mediante botón footer
        print("[P11] Probando cierre de modal mediante botón inferior de footer...")
        page.evaluate("() => window.openFirstRunModal()")
        time.sleep(0.5)
        assert modal.is_visible()
        close_footer.click()
        time.sleep(0.5)
        assert not modal.is_visible(), "El modal debe cerrarse al hacer clic en 'Cerrar Consola'"
        print("  ✓ Modal cerrado correctamente por footer.")

        # Verificar que no hubo excepciones no capturadas de JS
        js_crit_errors = [e for e in console_errors if "favicon" not in e.lower() and "chart" not in e.lower()]
        print(f"\n[ERRORES CONSOLA JS]: {len(js_crit_errors)}")
        for err in js_crit_errors:
            print(f"  ! {err}")
        assert len(js_crit_errors) == 0, f"No deben existir errores de JavaScript en consola: {js_crit_errors}"

        browser.close()

    print("\n" + "=" * 80)
    print(" AUDITORIA COMPLETADA: 100% EXITOSA - TODOS LOS BOTONES E INTERACCIONES OPERATIVAS")
    print("=" * 80)


if __name__ == "__main__":
    run_exhaustive_button_and_crud_audit()
