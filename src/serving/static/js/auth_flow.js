(function () {
  "use strict";

  const guestSession = () => ({ token: null, user: null, roles: ["readonly_viewer"], permissions: [] });

  window.activeSession = window.activeSession || guestSession();
  window.tempMfaToken = window.tempMfaToken || null;

  function setStatus(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
  }

  async function readPortOpsResponse(response) {
    if (window.readPortOpsResponse) return window.readPortOpsResponse(response);
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return response.json();
    const text = await response.text();
    return { detail: text || `Respuesta HTTP ${response.status}`, status: response.status };
  }

  function updateInspector(token, claims) {
    const rawEl = document.getElementById("inspector-token-raw");
    if (rawEl) rawEl.textContent = token || "No hay sesión activa autenticada.";
    const claimsEl = document.getElementById("inspector-token-claims");
    if (claimsEl) claimsEl.textContent = JSON.stringify(claims || {}, null, 2);
  }

  window.switchAuthTab = function (tabId) {
    document.querySelectorAll(".auth-tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-atab") === tabId);
    });
    document.querySelectorAll(".auth-tab-content").forEach(content => {
      content.classList.toggle("active", content.id === tabId);
    });
  };

  window.openAuthModal = async function (initialTab = "atab-login") {
    const modal = document.getElementById("auth-iam-modal");
    if (modal) {
      modal.classList.add("open");
      modal.style.display = "flex";
      modal.style.visibility = "visible";
      modal.style.opacity = "1";
      modal.style.pointerEvents = "auto";
    }
    window.switchAuthTab(initialTab);
  };

  window.closeAuthModal = function () {
    const modal = document.getElementById("auth-iam-modal");
    if (modal) {
      modal.classList.remove("open", "auth-force-visible");
      modal.style.display = "none";
      modal.style.visibility = "hidden";
      modal.style.opacity = "0";
      modal.style.pointerEvents = "none";
    }
    if (new URLSearchParams(window.location.search).get("auth") === "1") {
      window.history.replaceState({}, document.title, `${window.location.pathname}${window.location.hash || ""}`);
    }
  };

  window.closeFirstRunModal = function () {
    const modal = document.getElementById("first-run-setup-modal");
    if (modal) {
      modal.classList.remove("open");
      modal.style.display = "none";
      modal.style.visibility = "hidden";
      modal.style.opacity = "0";
      modal.style.pointerEvents = "none";
    }
  };

  window.syncSessionUI = window.syncSessionUI || function () {
    const isAuth = !!(window.activeSession && window.activeSession.token && window.activeSession.user);
    const user = isAuth ? window.activeSession.user : null;
    const role = isAuth ? (window.activeSession.roles[0] || "root") : "Invitado";
    const navUserLabel = document.getElementById("nav-user-label");
    if (navUserLabel) navUserLabel.textContent = isAuth ? `${user.username} (Salir)` : "Iniciar Sesión | Login In";
    const hudActiveRole = document.getElementById("hud-active-role");
    if (hudActiveRole) hudActiveRole.textContent = isAuth ? `Rol: ${role}` : "Modo: Invitado";
    const iamUserKpi = document.getElementById("iam-user-kpi");
    if (iamUserKpi) iamUserKpi.textContent = isAuth ? user.username : "Invitado";
    const iamRoleKpi = document.getElementById("iam-role-kpi");
    if (iamRoleKpi) iamRoleKpi.textContent = isAuth ? role : "readonly_viewer";
  };

  window.activateAuthenticatedSession = async function (data, statusElementId, options = {}) {
    if (!data || !data.session_token || !data.user) {
      throw new Error("La API no devolvió una sesión completa.");
    }

    window.activeSession.token = data.session_token;
    window.activeSession.user = data.user;
    window.activeSession.roles = data.roles || [];
    window.activeSession.permissions = data.permissions || [];
    localStorage.setItem("portops_token", data.session_token);

    const probe = await fetch("/api/v1/auth/me", {
      headers: { "Authorization": `Bearer ${data.session_token}` }
    });
    const sessionState = await probe.json().catch(() => ({}));
    if (!probe.ok || !sessionState.is_authenticated) {
      window.activeSession = guestSession();
      localStorage.removeItem("portops_token");
      window.syncSessionUI();
      throw new Error(sessionState.detail || "La sesión fue emitida pero no pasó la verificación activa.");
    }

    window.activeSession.user = {
      user_id: sessionState.user_id,
      username: sessionState.username,
      email: sessionState.email,
      full_name: sessionState.full_name || sessionState.username,
      is_root: !!sessionState.is_root
    };
    window.activeSession.roles = sessionState.roles || window.activeSession.roles;
    window.activeSession.permissions = sessionState.permissions || window.activeSession.permissions;
    window.syncSessionUI();
    updateInspector(data.session_token, {
      user: window.activeSession.user,
      roles: window.activeSession.roles,
      must_change_password: !!sessionState.must_change_password,
      exp: "12 Horas"
    });

    if (sessionState.must_change_password || data.must_change_password) {
      setStatus(statusElementId, `<span style="color:#f59e0b;">Sesión verificada. Cambio obligatorio de contraseña requerido.</span>`);
      window.switchAuthTab("atab-password");
      const oldPasswordInput = document.getElementById("pwd-input-old");
      const loginPasswordInput = document.getElementById("auth-input-password");
      if (oldPasswordInput && loginPasswordInput && loginPasswordInput.value) oldPasswordInput.value = loginPasswordInput.value;
      setStatus("pwd-change-status", `<span style="color:#f59e0b;">Actualice la contraseña temporal para habilitar el acceso operativo completo.</span>`);
      return;
    }

    setStatus(statusElementId, `<span style="color:#10b981;">${options.successMessage || "Sesion verificada y otorgada."}</span>`);
    setTimeout(() => window.closeAuthModal(), 700);
  };

  window.executeLogin = async function () {
    const username = document.getElementById("auth-input-username")?.value.trim() || "";
    const password = document.getElementById("auth-input-password")?.value || "";
    if (!username || !password) {
      setStatus("auth-login-status", `<span style="color:#f43f5e;">Ingrese usuario y contraseña.</span>`);
      return;
    }
    setStatus("auth-login-status", `<span style="color:#38bdf8;">Autenticando con PBKDF2...</span>`);
    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error en la autenticacion.");
      if (data.mfa_required) {
        window.tempMfaToken = data.temp_token;
        const mfaView = document.getElementById("auth-mfa-view");
        if (mfaView) mfaView.style.display = "block";
        setStatus("auth-login-status", `<span style="color:#f59e0b;">Desafio MFA requerido. Ingrese codigo TOTP.</span>`);
        return;
      }
      await window.activateAuthenticatedSession(data, "auth-login-status", {
        successMessage: `Sesion iniciada con exito. Bienvenido ${data.user.username}.`
      });
    } catch (err) {
      setStatus("auth-login-status", `<span style="color:#f43f5e;">Error: ${err.message}</span>`);
    }
  };

  window.executeVerifyMFA = async function () {
    const code = document.getElementById("auth-input-totp")?.value.replace(/\D/g, "") || "";
    if (code.length !== 6) {
      setStatus("auth-mfa-status", `<span style="color:#f43f5e;">Ingrese codigo de 6 digitos.</span>`);
      return;
    }
    if (!window.tempMfaToken) {
      setStatus("auth-mfa-status", `<span style="color:#f43f5e;">Primero ejecute Iniciar Sesion para generar el desafio MFA.</span>`);
      return;
    }
    setStatus("auth-mfa-status", `<span style="color:#38bdf8;">Verificando MFA y sesion activa...</span>`);
    try {
      const res = await fetch("/api/v1/auth/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_token: window.tempMfaToken, totp_code: code })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Codigo incorrecto.");
      window.tempMfaToken = null;
      await window.activateAuthenticatedSession(data, "auth-mfa-status", {
        successMessage: "MFA verificado. Sesion activa."
      });
    } catch (err) {
      setStatus("auth-mfa-status", `<span style="color:#f43f5e;">Error: ${err.message}</span>`);
    }
  };

  window.executeChangePassword = async function () {
    const oldInput = document.getElementById("pwd-input-old");
    const newInput = document.getElementById("pwd-input-new");
    const confirmInput = document.getElementById("pwd-input-confirm");
    if (!oldInput || !newInput || !confirmInput) return;
    if (newInput.value !== confirmInput.value) {
      setStatus("pwd-change-status", `<span style="color:#f43f5e;">Las contrasenas no coinciden.</span>`);
      return;
    }
    try {
      const headers = { "Content-Type": "application/json" };
      if (window.activeSession.token) headers.Authorization = `Bearer ${window.activeSession.token}`;
      const res = await fetch("/api/v1/auth/password/change", {
        method: "POST",
        headers,
        body: JSON.stringify({ old_password: oldInput.value, new_password: newInput.value })
      });
      const data = await readPortOpsResponse(res);
      if (!res.ok) throw new Error(data.detail || "Error al actualizar contraseña.");
      if (data.session_token) {
        localStorage.setItem("portops_token", data.session_token);
        window.activeSession.token = data.session_token;
      }
      if (window.activeSession.user) {
        window.activeSession.user.must_change_password = false;
      }
      window.syncSessionUI();
      setStatus("pwd-change-status", `<span style="color:#10b981;">${data.message || "Contraseña actualizada exitosamente."}</span>`);
      oldInput.value = "";
      newInput.value = "";
      confirmInput.value = "";
      setTimeout(() => window.closeAuthModal(), 900);
    } catch (err) {
      setStatus("pwd-change-status", `<span style="color:#f43f5e;">Error: ${err.message}</span>`);
    }
  };

  // Presets removed for production enterprise security compliance.

  document.addEventListener("click", (event) => {
    if (event.target.closest?.("#btn-auth-iam")) {
      window.openAuthModal("atab-login");
    }
  }, true);

  document.addEventListener("DOMContentLoaded", () => {
    if (new URLSearchParams(window.location.search).get("auth") === "1") window.openAuthModal("atab-login");
  });
})();
