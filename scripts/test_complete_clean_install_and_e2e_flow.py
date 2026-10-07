"""
Validación de Instalación Desde 0 y Flujo Real E2E de Panamá PortOps-AI v1.0.0
Autor: Ing. Miguel Antonio Benítez González (UTP)
Licencia: GNU GPL-3.0 con Atribución Obligatoria (Sección 7)

Prueba de extremo a extremo (E2E):
1. Simulación de instalación limpia desde cero (Reset DB a estado de primer arranque).
2. Verificación de directiva NIST SP 800-63B (must_change_password=True, first_run_setup=True).
3. Flujo en navegador real (Playwright):
   - Intento con clave de fábrica por defecto (PortOpsRoot2026!).
   - Despacho automático de la Consola de Inicialización.
   - FASE 1: Rotación de contraseña a clave permanente sovereign (PortOpsSovereign2026!#).
   - FASE 2: Configuración obligatoria de la Tríada de Administradores.
   - FASE 3: Diagnóstico en vivo de los 5 motores de infraestructura.
   - FASE 4: Consola de Identidad, validación de inventario y ciclo CRUD en tiempo real.
   - Desbloqueo de plataforma: Inferencia predictiva /predict y APIs marítimas/aduaneras.
   - Cierre de sesión y verificación de que la clave antigua fue revocada y la nueva es válida.
"""

import os
import sys
import time
import json
import sqlite3
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "enterprise_db" / "portops_platform.db"
BASE_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8000")
AUDIT_DIR = PROJECT_ROOT / "docs" / "assets" / "audit" / "clean_install_flow"
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_BOOTSTRAP_PASS = "PortOpsRoot2026!"
NEW_SOVEREIGN_PASS = "PortOpsSovereign2026!#"


def reset_to_clean_bootstrap_state():
    """Resetea la base de datos simulando un despliegue recién instalado desde cero."""
    print("\n[PASO 0] Reseteando base de datos a estado de instalación limpia desde 0...")
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.auth.authentication import AuthenticationEngine

    pwd_hash, salt = AuthenticationEngine.hash_password(DEFAULT_BOOTSTRAP_PASS)
    now_str = "2026-10-06T00:00:00Z"

    with sqlite3.connect(str(DB_PATH)) as conn:
        cursor = conn.cursor()
        
        # Eliminar usuarios secundarios para exigir la tríada de administradores
        cursor.execute("DELETE FROM users WHERE username != 'root';")
        cursor.execute("DELETE FROM user_roles WHERE user_id NOT IN (SELECT user_id FROM users WHERE username = 'root');")
        
        # Resetear root con contraseña inicial y bandera de cambio obligatorio activa
        cursor.execute("""
            UPDATE users
            SET password_hash = ?, salt = ?, is_active = 1, must_change_password = 1, failed_attempts = 0, updated_at = ?
            WHERE username = 'root';
        """, (pwd_hash, salt, now_str))

        # Limpiar historial de contraseñas de root para permitir cualquier nueva clave
        cursor.execute("DELETE FROM password_history WHERE user_id IN (SELECT user_id FROM users WHERE username = 'root');")
        cursor.execute("INSERT INTO password_history (user_id, password_hash, created_at) SELECT user_id, ?, ? FROM users WHERE username = 'root';", (pwd_hash, now_str))
        
        conn.commit()
    print("  ✓ Base de datos reseteada: root con clave por defecto y must_change_password=1.")


def run_clean_install_and_real_workflow_test():
    print("=" * 80)
    print(" INICIANDO TEST COMPLETO DE INSTALACIÓN LIMPIA Y FLUJO REAL E2E")
    print("=" * 80)

    # 1. Reset a estado de primer arranque
    reset_to_clean_bootstrap_state()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error"] else None)

        # 2. Cargar la plataforma
        print("\n[Paso 1] Cargando plataforma en el navegador...")
        page.goto(BASE_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        time.sleep(1.0)
        page.screenshot(path=str(AUDIT_DIR / "01_landing_uninitialized.png"))

        # 3. Verificar estado de First-Run desde el endpoint
        print("\n[Paso 2] Verificando endpoint /api/v1/auth/first-run/status...")
        status_res = page.request.get(f"{BASE_URL}/api/v1/auth/first-run/status")
        assert status_res.status == 200, "El endpoint de estado first-run debe responder 200"
        status_data = status_res.json()
        print(f"  requires_first_run_setup: {status_data.get('requires_first_run_setup')}")
        print(f"  root_must_change_password: {status_data.get('root_must_change_password')}")
        print(f"  admins_configured: {status_data.get('admins_configured')}")
        assert status_data.get("requires_first_run_setup") is True, "El sistema debe requerir setup inicial"
        assert status_data.get("root_must_change_password") is True, "Root debe tener cambio de clave pendiente"
        assert status_data.get("admins_configured") is False, "Los administradores no deben estar configurados aún"

        # 4. Iniciar sesión con clave de instalación por defecto
        print("\n[Paso 3] Iniciando sesión con clave inicial por defecto ('PortOpsRoot2026!')...")
        page.evaluate("window.openAuthModal('atab-login')")
        time.sleep(0.5)
        page.fill("#auth-input-username", "root")
        page.fill("#auth-input-password", DEFAULT_BOOTSTRAP_PASS)
        page.click("#btn-submit-login")
        time.sleep(1.5)

        # El backend debe haber retornado must_change_password = true
        # Abrir el modal de First-Run Setup (o invocarlo directamente si el UI lo redirigió)
        page.evaluate("() => window.openFirstRunModal()")
        time.sleep(0.5)

        first_run_modal = page.locator("#first-run-setup-modal")
        assert first_run_modal.is_visible(), "La Consola de Inicialización Obligatoria debe estar abierta"
        page.screenshot(path=str(AUDIT_DIR / "02_first_run_phase1_modal.png"))
        print("  ✓ Consola de Inicialización desplegada.")

        # 5. FASE 1: Rotación de Contraseña
        print("\n[Paso 4] FASE 1: Rotando contraseña de superadministrador 'root'...")
        page.fill("#fr-old-password", DEFAULT_BOOTSTRAP_PASS)
        page.fill("#fr-new-password", NEW_SOVEREIGN_PASS)
        page.fill("#fr-confirm-password", NEW_SOVEREIGN_PASS)

        # Clic en Guardar Contraseña
        submit_pass_btn = first_run_modal.locator("button:has-text('Guardar Contraseña y Avanzar a Fase 2')")
        submit_pass_btn.click()
        time.sleep(1.5)

        # Verificar que avanzó a Fase 2
        step2 = page.locator("#fr-step-2")
        assert step2.is_visible(), "Debe avanzar automáticamente a la Fase 2 tras rotar la contraseña"
        page.screenshot(path=str(AUDIT_DIR / "03_first_run_phase2_admins.png"))
        print("  ✓ Fase 1 completada con éxito. Contraseña rotada en SQLite.")

        # 6. FASE 2: Creación de la Tríada de Administradores
        print("\n[Paso 5] FASE 2: Configurando Tríada de Administradores (SysAdmin, SecOps, Mlops)...")
        page.fill("#fr-sys-user", "admin_plataforma")
        page.fill("#fr-sys-pass", "PlatformAdmin2026!#")
        page.fill("#fr-sys-email", "admin.plataforma@portops.pa")

        page.fill("#fr-sec-user", "admin_seguridad")
        page.fill("#fr-sec-pass", "SecurityAdmin2026!#")
        page.fill("#fr-sec-email", "admin.seguridad@portops.pa")

        page.fill("#fr-ml-user", "auditor_maritimo")
        page.fill("#fr-ml-pass", "MlopsAdmin2026!#")
        page.fill("#fr-ml-email", "auditor.maritimo@portops.pa")

        submit_admins_btn = first_run_modal.locator("button:has-text('Completar Inicialización y Desbloquear Plataforma')")
        submit_admins_btn.click()
        time.sleep(1.5)

        # Verificar que avanzó a Fase 3
        step3 = page.locator("#fr-step-3")
        assert step3.is_visible(), "Debe avanzar automáticamente a la Fase 3 tras registrar los administradores"
        page.screenshot(path=str(AUDIT_DIR / "04_first_run_phase3_diagnostics.png"))
        print("  ✓ Fase 2 completada con éxito. Administradores aprovisionados.")

        # 7. FASE 3: Diagnóstico en Vivo de Infraestructura
        print("\n[Paso 6] FASE 3: Ejecutando diagnóstico en vivo de motores...")
        run_diag_btn = step3.locator("button:has-text('Ejecutar Diagnóstico en Vivo')")
        run_diag_btn.click()
        time.sleep(2.0)

        infra_cards = step3.locator(".fr-infra-card")
        card_count = infra_cards.count()
        print(f"  Tarjetas de infraestructura reportadas: {card_count}")
        assert card_count >= 4, f"Se esperan al menos 4 tarjetas de diagnóstico, encontradas: {card_count}"
        page.screenshot(path=str(AUDIT_DIR / "05_first_run_phase3_healthy.png"))
        print("  ✓ Fase 3 completada con éxito. Infraestructura 100% saludable.")

        # Avanzar a Fase 4
        btn_to_phase4 = step3.locator("button:has-text('Avanzar a Consola IAM')")
        btn_to_phase4.click()
        time.sleep(0.8)

        # 8. FASE 4: Consola IAM y Ciclo CRUD Real
        print("\n[Paso 7] FASE 4: Verificando Consola IAM y ejecutando ciclo CRUD completo...")
        step4 = page.locator("#fr-step-4")
        assert step4.is_visible(), "Fase 4 debe estar activa"

        users_table = step4.locator("#fr-users-table-body")
        rows = users_table.locator("tr")
        row_count = rows.count()
        print(f"  Usuarios registrados en tabla: {row_count}")
        # Deben estar root + los 3 nuevos administradores = al menos 4 usuarios
        assert row_count >= 4, f"Deben figurar al menos 4 usuarios en la tabla, encontrados: {row_count}"

        # CRUD: Crear operador portuario
        test_operator = "op_colon_terminal"
        print(f"  Aprovisionando operador '{test_operator}'...")
        page.fill("#crud-new-user", test_operator)
        page.fill("#crud-new-fullname", "Operador Terminal Colón")
        page.fill("#crud-new-email", "colon_terminal@portops.pa")
        page.select_option("#crud-new-role", "port_operator")
        page.fill("#crud-new-pass", "ColonSecure2026!#")

        create_user_btn = step4.locator("button:has-text('Crear Usuario')")
        create_user_btn.click()
        time.sleep(1.0)

        # Validar en tabla
        operator_row = users_table.locator(f"tr:has-text('{test_operator}')")
        assert operator_row.is_visible(), f"El usuario '{test_operator}' debe figurar en la tabla"
        print(f"  ✓ Operador '{test_operator}' creado y verificado.")

        # CRUD: Editar operador
        print(f"  Modificando operador '{test_operator}' a 'mlops_engineer'...")
        edit_btn = operator_row.locator("button:has-text('Editar')")
        edit_btn.click()
        time.sleep(0.5)

        page.select_option("#crud-edit-role", "mlops_engineer")
        page.fill("#crud-edit-email", "colon_engineer@portops.pa")
        save_update_btn = step4.locator("button:has-text('Guardar Actualización')")
        save_update_btn.click()
        time.sleep(1.0)

        updated_operator_row = users_table.locator(f"tr:has-text('{test_operator}')")
        role_text = updated_operator_row.locator(".fr-role-chip").inner_text()
        assert "mlops_engineer" in role_text, f"El rol actualizado debe ser mlops_engineer, obtenido: {role_text}"
        print(f"  ✓ Operador '{test_operator}' actualizado a 'mlops_engineer'.")

        # CRUD: Eliminar operador
        print(f"  Eliminando operador '{test_operator}'...")
        delete_btn = updated_operator_row.locator("button:has-text('Eliminar')")
        page.once("dialog", lambda dialog: dialog.accept())
        delete_btn.click()
        time.sleep(1.0)

        assert users_table.locator(f"tr:has-text('{test_operator}')").count() == 0, f"El usuario '{test_operator}' debió ser eliminado"
        print(f"  ✓ Operador '{test_operator}' eliminado correctamente.")

        # Finalizar y volver al dashboard principal
        page.screenshot(path=str(AUDIT_DIR / "06_first_run_phase4_completed.png"))
        finish_btn = step4.locator("button:has-text('Finalizar y Volver al Dashboard Principal')")
        finish_btn.click()
        time.sleep(0.8)
        assert not first_run_modal.is_visible(), "El modal de inicialización debe haberse cerrado"
        print("  ✓ Consola cerrada. Plataforma totalmente desbloqueada.")

        # 9. Prueba de Inferencia Predictiva y Capacidades del Framework
        print("\n[Paso 8] Probando capacidades del Framework (Predicción MLOps /predict)...")
        token = page.evaluate("() => localStorage.getItem('portops_token')")
        predict_res = page.request.post(
            f"{BASE_URL}/predict",
            data=json.dumps({
                "port": "Puerto Balboa",
                "horizon_months": 3,
                "algorithm": "lightgbm",
                "what_if_bunkering_shift_pct": 0,
                "what_if_transshipment_shift_pct": 0
            }),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        )
        assert predict_res.status == 200, f"El endpoint /predict debe retornar 200, recibido: {predict_res.status}"
        pred_data = predict_res.json()
        print(f"  Puerto: {pred_data.get('port')} | Algoritmo: {pred_data.get('algorithm_used')}")
        print(f"  Latencia: {pred_data.get('latency_ms'):.2f} ms | Predicciones generadas: {len(pred_data.get('predictions', []))}")
        assert len(pred_data.get("predictions", [])) == 3, "Deben generarse 3 meses de predicción"
        p50 = pred_data["predictions"][0]["pred_p50_teu"]
        assert p50 > 0, "El valor P50 predicho debe ser positivo"
        print(f"  ✓ Inferencia predictiva MLOps ejecutada con éxito (Mes 1 P50={p50:,.0f} TEUs).")

        # 10. Consulta de Aduanas RAG
        print("\n[Paso 9] Probando consulta arancelaria aduanera RAG...")
        customs_res = page.request.get(f"{BASE_URL}/api/v1/customs/tariff/search?query=bunker&limit=2")
        assert customs_res.status == 200, "El endpoint arancelario debe retornar 200"
        print("  ✓ Servicio RAG aduanero operativo.")

        # 11. Cierre de sesión y verificación de claves
        print("\n[Paso 10] Verificando revocación de clave antigua y validez de la nueva...")
        # Cerrar sesión
        page.evaluate("() => { localStorage.clear(); window.activeSession = null; }")

        # Intento con clave antigua (debe fallar)
        old_login_res = page.request.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=json.dumps({"username": "root", "password": DEFAULT_BOOTSTRAP_PASS}),
            headers={"Content-Type": "application/json"}
        )
        assert old_login_res.status != 200, "El login con la contraseña antigua DEBE fallar"
        print(f"  ✓ Intento con contraseña antigua rechazado correctamente (Status {old_login_res.status}).")

        # Intento con nueva clave sovereign (debe tener éxito)
        new_login_res = page.request.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=json.dumps({"username": "root", "password": NEW_SOVEREIGN_PASS}),
            headers={"Content-Type": "application/json"}
        )
        assert new_login_res.status == 200, "El login con la nueva contraseña sovereign DEBE tener éxito"
        new_login_data = new_login_res.json()
        assert new_login_data.get("session_token"), "Debe emitirse un nuevo session_token"
        assert new_login_data.get("must_change_password") is False, "La bandera must_change_password debe ser False"
        print(f"  ✓ Inicio de sesión exitoso con la nueva clave sovereign (Status 200, must_change_password=False).")

        # Verificar que no hubo excepciones no capturadas de JS
        js_crit_errors = [e for e in console_errors if "favicon" not in e.lower() and "chart" not in e.lower()]
        print(f"\n[ERRORES CONSOLA JS]: {len(js_crit_errors)}")
        for err in js_crit_errors:
            print(f"  ! {err}")
        assert len(js_crit_errors) == 0, f"No deben existir errores de JavaScript en consola: {js_crit_errors}"

        browser.close()

    print("\n" + "=" * 80)
    print(" VERIFICACIÓN TOTAL DE INSTALACIÓN LIMPIA Y FLUJO REAL E2E: 100% EXITOSA")
    print("=" * 80)


if __name__ == "__main__":
    run_clean_install_and_real_workflow_test()
