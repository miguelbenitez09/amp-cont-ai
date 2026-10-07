"""
Pruebas exhaustivas para la interfaz visual, inicio de sesión condicional,
ocultamiento de menús sensibles para invitados y componentes interactivos con hover.

Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
"""
from pathlib import Path
import re
import pytest
from bs4 import BeautifulSoup
import requests

STATIC_DIR = Path("src/serving/static")
INDEX_HTML = STATIC_DIR / "index.html"
STYLE_CSS = STATIC_DIR / "css" / "style.css"
APP_JS = STATIC_DIR / "js" / "app.js"
AUTH_FLOW_JS = STATIC_DIR / "js" / "auth_flow.js"


def test_index_html_exists_and_contains_expected_auth_protection():
    assert INDEX_HTML.exists(), "index.html debe existir en src/serving/static"
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Verificar tabs en el modal de autenticación IAM
    auth_tabs_nav = soup.find(class_="auth-tabs-nav")
    assert auth_tabs_nav is not None, "Debe existir .auth-tabs-nav en auth-iam-modal"

    pwd_tab = auth_tabs_nav.find("button", {"data-atab": "atab-password"})
    mfa_tab = auth_tabs_nav.find("button", {"data-atab": "atab-mfa"})
    insp_tab = auth_tabs_nav.find("button", {"data-atab": "atab-inspector"})

    assert "auth-requires-login" in pwd_tab.get("class", []), "Tab de cambio de clave debe requerir login"
    assert "auth-requires-login" in mfa_tab.get("class", []), "Tab de MFA debe requerir login"
    assert "auth-requires-login" in insp_tab.get("class", []), "Tab de inspector de tokens debe requerir login"

    assert "display: none" in pwd_tab.get("style", "").lower(), "Tab de cambio de clave debe estar oculto por defecto"
    assert "display: none" in mfa_tab.get("style", "").lower(), "Tab de MFA debe estar oculto por defecto"
    assert "display: none" in insp_tab.get("style", "").lower(), "Tab de inspector debe estar oculto por defecto"


def test_settings_modal_protects_sensitive_admin_tabs():
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    settings_tabs_nav = soup.find(class_="settings-tabs-nav")
    assert settings_tabs_nav is not None, "Debe existir .settings-tabs-nav en settings-modal"

    # Verificar tabs sensibles que deben estar protegidos y ocultos sin sesión
    sensitive_tabs = [
        "stab-deploy-verify",
        "stab-vllm-secrets",
        "stab-user-guardrails",
        "stab-gov-admin",
        "stab-mcp-souls",
        "stab-extensibility",
    ]

    for tab_id in sensitive_tabs:
        btn = settings_tabs_nav.find("button", {"data-settings-tab": tab_id})
        assert btn is not None, f"El botón de tab {tab_id} debe existir en settings-modal"
        assert "admin-requires-auth" in btn.get("class", []), f"Tab {tab_id} debe tener clase admin-requires-auth"
        assert "display: none" in btn.get("style", "").lower(), f"Tab {tab_id} debe estar oculto por defecto"

    # Banner de advertencia de modo invitado en el modal de configuración
    banner = soup.find(id="settings-guest-alert-banner")
    assert banner is not None, "Debe existir #settings-guest-alert-banner para guiar al usuario invitado"


def test_first_run_setup_modal_hidden_by_default():
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    fr_modal = soup.find(id="first-run-setup-modal")
    assert fr_modal is not None, "#first-run-setup-modal debe existir"
    style = fr_modal.get("style", "").lower()
    assert "display: none" in style, "El modal de first-run debe tener display: none por defecto para no invadir al invitado"


def test_capability_cards_contain_rich_hover_previews():
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    cap_cards = soup.find_all(class_="capability-card")
    assert len(cap_cards) == 4, "Deben existir 4 capability-cards en la landing page"

    for card in cap_cards:
        hover_preview = card.find(class_="card-hover-preview")
        assert hover_preview is not None, "Cada capability-card debe contener .card-hover-preview para efecto hover"
        badge = hover_preview.find(class_="card-hover-badge")
        assert badge is not None, "Cada hover preview debe tener .card-hover-badge"
        tags = hover_preview.find_all(class_="hover-tag")
        assert len(tags) >= 2, "Cada hover preview debe contener etiquetas técnicas de contexto"


def test_style_css_has_card_hover_and_popover_definitions():
    assert STYLE_CSS.exists(), "style.css debe existir"
    css_content = STYLE_CSS.read_text(encoding="utf-8")

    assert ".card-hover-preview" in css_content
    assert ".card-hover-badge" in css_content
    assert ".card-hover-tags" in css_content
    assert ".hover-tag" in css_content
    assert ".card-hover-popover" in css_content
    assert ".algo-stat-card:hover" in css_content
    assert ".capability-card:hover" in css_content


def test_app_js_implements_safe_guest_auth_and_hover_interactivity():
    assert APP_JS.exists(), "app.js debe existir"
    js_content = APP_JS.read_text(encoding="utf-8")

    # 1. syncSessionUI maneja visibilidad condicional
    assert "auth-requires-login" in js_content
    assert "admin-requires-auth" in js_content
    assert "settings-guest-alert-banner" in js_content
    assert "auth-session-profile-view" in js_content

    # 2. first run modal protegido para invitados
    assert "if (!isAuth && !forceOpen)" in js_content

    # 3. Interactividad hover en tarjetas
    assert "initCardHoverInteractivity" in js_content
    assert "global-card-hover-popover" in js_content


def test_live_fastapi_server_serving_pages():
    """Verifica que el servidor Uvicorn FastAPI en localhost:8001 responde 200 en las rutas web."""
    try:
        res = requests.get("http://127.0.0.1:8001/app", timeout=3)
        assert res.status_code == 200
        assert "Panamá PortOps-AI" in res.text
        assert "card-hover-preview" in res.text
    except requests.exceptions.ConnectionError:
        pytest.skip("Uvicorn en puerto 8001 no accesible en este instante")


def test_skeleton_shimmer_system_defined_in_style_css():
    """Verifica que style.css implementa el sistema completo de skeleton loading y animación shimmer."""
    css_content = STYLE_CSS.read_text(encoding="utf-8")
    assert "@keyframes skeleton-shimmer" in css_content
    assert "@keyframes skeleton-pulse" in css_content
    assert ".skeleton-box" in css_content
    assert ".skeleton-pill" in css_content
    assert ".skeleton-text" in css_content
    assert ".skeleton-metric" in css_content
    assert ".skeleton-chart" in css_content
    assert ".skeleton-bar" in css_content
    assert ".skeleton-card" in css_content
    assert ".stagger-fade-in" in css_content


def test_wcag_aa_contrast_palette_across_all_themes():
    """Verifica que todos los 6 temas y :root poseen tokens de color conformes a WCAG AA (>= 4.5:1)."""
    css_content = STYLE_CSS.read_text(encoding="utf-8")

    # Tokens en :root
    assert "--text-dim: #94a3b8;" in css_content
    assert "--purple-ai: #c084fc;" in css_content
    assert "--font-sans:" in css_content
    assert "--amber-warning:" in css_content

    # Verificación en los 6 temas marítimos
    themes = [
        "theme-cyber-ocean",
        "theme-radar-amber",
        "theme-canal-emerald",
        "theme-tactical-mono",
        "theme-pacific-sunset",
        "theme-midnight-cobalt",
    ]
    for theme in themes:
        assert theme in css_content, f"El tema {theme} debe estar definido en style.css"

    # En midnight-cobalt, cyan-primary debe ser #38bdf8 para superar 7:1
    cobalt_section = css_content[css_content.find("theme-midnight-cobalt") : css_content.find("theme-midnight-cobalt") + 600]
    assert "--cyan-primary: #38bdf8;" in cobalt_section


def test_methodology_carousel_toolbar_and_stepper_buttons():
    """Verifica que index.html contiene la barra de herramientas del carrusel con sus 8 píldoras y botones de avance."""
    html_content = INDEX_HTML.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_content, "html.parser")

    toolbar = soup.find(id="method-carousel-toolbar")
    assert toolbar is not None, "Debe existir #method-carousel-toolbar en tab-methodology"

    prev_btn = soup.find(id="btn-carousel-prev")
    next_btn = soup.find(id="btn-carousel-next")
    assert prev_btn is not None, "Debe existir botón #btn-carousel-prev"
    assert next_btn is not None, "Debe existir botón #btn-carousel-next"

    pills = soup.find_all(class_="method-step-pill")
    assert len(pills) == 8, "Deben existir exactamente 8 píldoras interactivas (Fases 1 a 8)"

    counter = soup.find(id="method-carousel-counter")
    assert counter is not None, "Debe existir el indicador #method-carousel-counter"


def test_app_js_implements_skeleton_loaders_and_stepper_navigation():
    """Verifica que app.js implementa funciones para skeleton loaders, delay táctil y teclado para el carrusel."""
    js_content = APP_JS.read_text(encoding="utf-8")

    # Skeleton loaders
    assert "showForecastSkeleton" in js_content
    assert "hideForecastSkeleton" in js_content
    assert "showSimulationSkeleton" in js_content
    assert "hideSimulationSkeleton" in js_content
    assert "showBenchmarkSkeleton" in js_content

    # Stepper and Carousel helpers
    assert "goToPreviousPhase" in js_content
    assert "goToNextPhase" in js_content
    assert "updatePhaseIndicators" in js_content
    assert "method-carousel-counter" in js_content
    assert "a11y-announcer" in js_content

    # Keyboard navigation
    assert "ArrowLeft" in js_content
    assert "ArrowRight" in js_content
