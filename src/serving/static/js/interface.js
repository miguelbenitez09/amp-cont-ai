/* Navigation presentation only: feature handlers remain owned by app.js. */
(function () {
  "use strict";
  window.presentInterfacePanel = function(panel) {
    if (!panel) return;
    const surface = panel.matches(".modal-backdrop") ? panel.querySelector(".modal-dialog") || panel : panel;
    surface.getAnimations().forEach(animation => animation.cancel());
    if (!matchMedia("(prefers-reduced-motion: reduce)").matches) {
      surface.animate([{opacity:0,transform:"translateY(5px)"},{opacity:1,transform:"translateY(0)"}], {
        duration:200,easing:"cubic-bezier(.2,.7,.2,1)"
      });
    }
    requestAnimationFrame(() => {
      if (!panel.classList.contains("active")) return;
      for (const canvas of panel.querySelectorAll("canvas")) {
        const chart = window.Chart?.getChart(canvas);
        if (chart) { chart.stop(); chart.resize(); chart.update("none"); }
      }
    });
  };
  document.addEventListener("DOMContentLoaded", () => {
    const nav = document.querySelector(".ops-app main > .tabs-nav");
    const toggle = document.getElementById("workspace-navigation-toggle");
    if (!nav || !toggle) return;
    const label = toggle.querySelector("span");
    const railToggle = document.createElement("button");
    railToggle.type = "button";
    railToggle.id = "sidebar-toggle";
    railToggle.className = "sidebar-toggle";
    railToggle.setAttribute("aria-controls", nav.id);
    railToggle.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="3" y="4" width="18" height="16" rx="3"/><path d="M9 4v16"/></svg><span class="sidebar-toggle-label">Navegación</span>';
    nav.prepend(railToggle);
    let collapsed = false;
    try { collapsed = localStorage.getItem("portops-sidebar-collapsed") === "true"; } catch {}
    function setCollapsed(value) {
      collapsed = value;
      document.body.classList.toggle("ops-sidebar-collapsed", value);
      railToggle.setAttribute("aria-expanded", String(!value));
      railToggle.setAttribute("aria-label", value ? "Expandir barra lateral" : "Contraer barra lateral");
      railToggle.title = (value ? "Expandir" : "Contraer") + " barra lateral (Ctrl+Shift+S)";
      try { localStorage.setItem("portops-sidebar-collapsed", String(value)); } catch {}
    }
    railToggle.addEventListener("click", () => setCollapsed(!collapsed));
    document.addEventListener("keydown", event => {
      if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === "s" && !document.querySelector(".modal-backdrop.open")) {
        event.preventDefault();
        if (matchMedia("(max-width:800px)").matches) toggle.click();
        else setCollapsed(!collapsed);
      }
    });
    setCollapsed(collapsed);
    function sync() {
      const active = nav.querySelector(".tab-btn.active");
      label.textContent = active?.textContent.trim() || "NavegaciÃ³n";
      for (const button of nav.querySelectorAll(".tab-btn")) {
        const selected = button === active;
        button.setAttribute("aria-current", selected ? "page" : "false");
        button.setAttribute("aria-controls", button.dataset.tab);
        button.setAttribute("aria-label", button.textContent.trim());
        button.title = button.textContent.trim();
      }
    }
    toggle.addEventListener("click", () => {
      const expanded = document.body.classList.toggle("ops-navigation-open");
      toggle.setAttribute("aria-expanded", String(expanded));
    });
    nav.addEventListener("click", event => {
      if (!event.target.closest(".tab-btn")) return;
      queueMicrotask(() => {
        document.body.classList.remove("ops-navigation-open");
        toggle.setAttribute("aria-expanded", "false");
        sync();
        if (matchMedia("(max-width: 800px)").matches) toggle.focus();
        window.scrollTo({ top: 0, behavior: "auto" });
      });
    });
    new MutationObserver(sync).observe(nav, { subtree: true, attributes: true, attributeFilter: ["class"], childList: true });
    const observer = new MutationObserver(records => {
      for (const record of records) {
        const panel = record.target;
        if (panel.matches(".tab-content.active,.settings-tab-content.active,.auth-tab-content.active,.modal-backdrop.open")) {
          window.presentInterfacePanel(panel);
        }
      }
    });
    document.querySelectorAll(".tab-content,.settings-tab-content,.auth-tab-content,.modal-backdrop").forEach(panel => {
      observer.observe(panel, {attributes:true,attributeFilter:["class"]});
    });
    sync();
  });
})();
