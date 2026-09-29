/**
 * Panamá PortOps-AI v1.0 - Modular i18n Translation Engine
 * Desarrollado v1.0.0 Miguel Benítez | GNU GPL v3.0
 */

(function() {
  const STORAGE_KEY = "portops_user_language";
  
  const I18nManager = {
    currentLang: "es",
    dictionaries: {},

    init() {
      this.dictionaries["es"] = window.I18N_ES || {};
      this.dictionaries["en"] = window.I18N_EN || {};
      this.dictionaries["pt"] = window.I18N_PT || {};

      // Determine starting language from localStorage or navigator
      const savedLang = localStorage.getItem(STORAGE_KEY);
      if (savedLang && (savedLang === "es" || savedLang === "en" || savedLang === "pt")) {
        this.currentLang = savedLang;
      } else {
        const navLang = (navigator.language || "").toLowerCase();
        if (navLang.startsWith("pt")) {
          this.currentLang = "pt";
        } else if (navLang.startsWith("en")) {
          this.currentLang = "en";
        } else {
          this.currentLang = "es";
        }
      }

      // Initial DOM translation
      this.translateDOM();
      this.syncLanguageControls();
    },

    setLanguage(lang) {
      if (lang !== "es" && lang !== "en" && lang !== "pt") return;
      this.currentLang = lang;
      localStorage.setItem(STORAGE_KEY, lang);
      document.documentElement.lang = lang;
      this.translateDOM();
      this.syncLanguageControls();

      // Dispatch custom event for dynamic components to update
      window.dispatchEvent(new CustomEvent("portopsLanguageChanged", {
        detail: { language: lang }
      }));
    },

    getLanguage() {
      return this.currentLang;
    },

    t(keyPath, fallback = "") {
      if (!keyPath) return fallback;
      const dict = this.dictionaries[this.currentLang] || this.dictionaries["es"] || {};
      const keys = keyPath.split(".");
      let val = dict;
      for (const k of keys) {
        if (val && typeof val === "object" && k in val) {
          val = val[k];
        } else {
          // Fallback to Spanish if missing in current language
          let esVal = this.dictionaries["es"];
          for (const ek of keys) {
            if (esVal && typeof esVal === "object" && ek in esVal) {
              esVal = esVal[ek];
            } else {
              esVal = null;
              break;
            }
          }
          return esVal !== null && esVal !== undefined ? esVal : (fallback || keyPath);
        }
      }
      return val !== null && val !== undefined ? val : (fallback || keyPath);
    },

    translateDOM() {
      // 0. Update document title
      const appTitle = this.t("nav.app_title", "Panamá PortOps-AI");
      document.title = `${appTitle} v1.0.0 | developed by Miguel Benítez`;

      // 1. Text elements with data-i18n
      const elements = document.querySelectorAll("[data-i18n]");
      elements.forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (key) {
          const translation = this.t(key);
          if (translation) {
            el.innerHTML = translation;
          }
        }
      });

      // 2. Input placeholders with data-i18n-placeholder
      const placeholderElements = document.querySelectorAll("[data-i18n-placeholder]");
      placeholderElements.forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (key) {
          const translation = this.t(key);
          if (translation) {
            el.placeholder = translation;
          }
        }
      });

      // 3. Titles / tooltips with data-i18n-title
      const titleElements = document.querySelectorAll("[data-i18n-title]");
      titleElements.forEach(el => {
        const key = el.getAttribute("data-i18n-title");
        if (key) {
          const translation = this.t(key);
          if (translation) {
            el.title = translation;
          }
        }
      });
    },

    syncLanguageControls() {
      const select = document.getElementById("nav-lang-select");
      if (select) {
        select.value = this.currentLang;
        if (!select.dataset.bound) {
          select.dataset.bound = "true";
          select.addEventListener("change", (e) => this.setLanguage(e.target.value));
        }
      }
      const toggleBtn = document.getElementById("btn-lang-toggle");
      if (toggleBtn) {
        toggleBtn.textContent = this.currentLang === "es" ? "🌐 ES / EN" : "🌐 EN / ES";
      }
    }
  };

  // Expose globally
  window.I18n = I18nManager;
  window.t = function(key, fallback) {
    return I18nManager.t(key, fallback);
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => I18nManager.init());
  } else {
    I18nManager.init();
  }
})();
