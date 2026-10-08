/* Shared session transport and accessible IAM dialog lifecycle. */
(function () {
  "use strict";
  // Remove credentials persisted by older versions. Sessions now restore through HttpOnly cookies.
  try { localStorage.removeItem("portops_token"); } catch (error) { console.warn("No se pudo limpiar el almacenamiento de sesión."); }
  window.portopsCsrfToken = null;
  const originalFetch = window.fetch.bind(window);
  window.fetch = async function (input, init = {}) {
    const request = new Request(input, init);
    const url = new URL(request.url);
    let response;
    if (url.origin === location.origin && !["GET", "HEAD", "OPTIONS"].includes(request.method)) {
      if (!window.portopsCsrfToken) await window.refreshPortOpsSession?.();
      const retryRequest = request.clone();
      const headers = new Headers(request.headers);
      if (window.portopsCsrfToken) headers.set("X-CSRF-Token", window.portopsCsrfToken);
      response = await originalFetch(new Request(request, { headers }));
      if (response.status === 403) {
        const failure = await response.clone().json().catch(() => null);
        if (failure?.code === "browser_request_rejected") {
          await window.refreshPortOpsSession?.();
          const retryHeaders = new Headers(retryRequest.headers);
          if (window.portopsCsrfToken) retryHeaders.set("X-CSRF-Token", window.portopsCsrfToken);
          else retryHeaders.delete("X-CSRF-Token");
          response = await originalFetch(new Request(retryRequest, { headers: retryHeaders }));
        }
      }
    } else {
      response = await originalFetch(request);
    }
    if (url.origin === location.origin && response.headers.has("X-CSRF-Token")) {
      window.portopsCsrfToken = response.headers.get("X-CSRF-Token");
    }
    return response;
  };
  window.refreshPortOpsSession = async function () {
    try {
      const response = await fetch("/api/v1/auth/me", { credentials: "same-origin", cache: "no-store" });
      if (!response.ok) throw new Error(`Sesión no disponible (${response.status})`);
      const session = await response.json();
      window.portopsCsrfToken = session.csrf_token || null;
      window.activeSession = session.is_authenticated ? {
        token: null,
        user: { user_id: session.user_id, username: session.username, email: session.email,
          is_root: session.is_root, must_change_password: session.must_change_password },
        roles: session.roles || [], permissions: session.permissions || []
      } : { token: null, user: null, roles: ["readonly_viewer"], permissions: [] };
    } catch (error) {
      window.portopsCsrfToken = null;
      window.activeSession = { token: null, user: null, roles: ["readonly_viewer"], permissions: [] };
      console.warn("No se pudo verificar la sesión; vuelva a iniciar sesión.", error.message);
    }
    window.syncSessionUI?.();
    return window.activeSession;
  };

  let returnFocus = null;
  const inertBefore = new Map();
  const visibleControls = modal => [...modal.querySelectorAll("button,input,select,textarea,a[href],[tabindex]")]
    .filter(el => !el.disabled && el.tabIndex >= 0 && el.getClientRects().length && getComputedStyle(el).visibility !== "hidden");
  window.focusPortOpsAuthDialog = function () {
    const modal = document.getElementById("auth-iam-modal");
    if (!modal) return;
    if (!modal.contains(document.activeElement)) returnFocus = document.activeElement;
    if (modal.parentElement !== document.body) document.body.appendChild(modal);
    for (const element of document.body.children) {
      if (element === modal) continue;
      if (!inertBefore.has(element)) inertBefore.set(element, element.inert);
      element.inert = true;
    }
    if (!modal.contains(document.activeElement)) {
      const input = modal.querySelector("#auth-input-username");
      (input?.getClientRects().length ? input : visibleControls(modal)[0] || modal).focus();
    }
  };
  window.releasePortOpsAuthDialog = function () {
    for (const [element, wasInert] of inertBefore) element.inert = wasInert;
    inertBefore.clear();
    if (returnFocus?.isConnected) returnFocus.focus();
    returnFocus = null;
  };
  document.addEventListener("keydown", event => {
    const modal = document.getElementById("auth-iam-modal");
    if (!modal?.classList.contains("open")) return;
    if (event.key === "Escape") {
      event.preventDefault(); event.stopImmediatePropagation(); window.closeAuthModal();
    } else if (event.key === "Tab") {
      const controls = visibleControls(modal);
      const first = controls[0] || modal, last = controls[controls.length - 1] || modal;
      if (event.shiftKey && (document.activeElement === first || !modal.contains(document.activeElement))) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && (document.activeElement === last || !modal.contains(document.activeElement))) {
        event.preventDefault(); first.focus();
      }
    }
  }, true);
})();
