/**
 * Panamá PortOps-AI v1.0.0 - Motor de Recorrido Guiado Interactivo (Interactive Tour)
 * Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
 * 
 * Componente modular, accesible (WCAG 2.2 AA) y multilingüe (ES/EN/PT).
 * Permite a operadores portuarios, analistas y auditores explorar inmersivamente
 * cada capacidad del sistema sin dependencias externas.
 */

(function () {
  'use strict';

  const TOUR_STEPS = [
    {
      id: 'step-hero',
      target: '.landing-hero',
      tab: 'tab-landing',
      placement: 'bottom',
      titleKey: 'tour.step_hero_title',
      titleDefault: 'Hub Marítimo & MLOps Soberano de Panamá',
      descKey: 'tour.step_hero_desc',
      descDefault: 'Bienvenido a la plataforma industrial de analítica logística, orquestación de agentes de IA y benchmarking multi-algoritmo. Aquí supervisas los 6 puertos nacionales, el canal interoceánico y el flujo comercial exterior.'
    },
    {
      id: 'step-controls',
      target: '#nav-lang-select',
      targetContainer: '.nav-control-group:first-child',
      tab: null,
      placement: 'bottom',
      titleKey: 'tour.step_controls_title',
      titleDefault: 'Idiomas & Paleta Visual Náutica',
      descKey: 'tour.step_controls_desc',
      descDefault: 'Personaliza tu entorno en tiempo real. Alterna entre Español, Inglés y Portugués, y elige entre 6 temas marítimos de alto contraste (Atlántico Cian, Radar Ámbar, Cuenca Esmeralda, Pacífico Sunset, etc.).'
    },
    {
      id: 'step-iam',
      target: '#btn-auth-iam',
      tab: null,
      placement: 'bottom',
      titleKey: 'tour.step_iam_title',
      titleDefault: 'Centro de Seguridad IAM & Roles RBAC',
      descKey: 'tour.step_iam_desc',
      descDefault: 'Motor de autorización estricta con 31 capacidades auditables, autenticación multifactor MFA (RFC 6238 TOTP) y roles segmentados para auditores, operadores y científicos de datos.'
    },
    {
      id: 'step-worm',
      target: '#hud-worm-status',
      tab: null,
      placement: 'bottom',
      titleKey: 'tour.step_worm_title',
      titleDefault: 'Integridad Criptográfica WORM SHA-256',
      descKey: 'tour.step_worm_desc',
      descDefault: 'Libro inmutable Write-Once-Read-Many encadenado por hashes SHA-256. Cada inferencia, consulta fiscal y transacción queda sellada de forma infalsificable bajo Ley 6 de 2002.'
    },
    {
      id: 'step-cot',
      target: '#tab-btn-cot',
      activeTabTarget: '#cot-chat-thread',
      tab: 'tab-cot-swarm',
      placement: 'bottom',
      titleKey: 'tour.step_cot_title',
      titleDefault: 'Enjambre Agéntico & Razonamiento CoT',
      descKey: 'tour.step_cot_desc',
      descDefault: 'Orquestación de agentes autónomos con almas criptográficas (Aduanas, Logística, Cuantiles, Seguridad). Visualiza trazas CoT paso a paso, guardrails anti-inyección y respuestas fundamentadas.'
    },
    {
      id: 'step-customs',
      target: '#tab-btn-customs',
      activeTabTarget: '#tab-customs-lakehouse .customs-banner',
      tab: 'tab-customs-lakehouse',
      placement: 'bottom',
      titleKey: 'tour.step_customs_title',
      titleDefault: 'Aduanas, RAG Arancelario & Lakehouse 5D',
      descKey: 'tour.step_customs_desc',
      descDefault: 'Motor de búsqueda vectorial y semántica sobre el Arancel Nacional del SAC y declaraciones DUA. Calcula impuestos DAI/ITBMS y audita microdatos reales en capas Bronze, Silver y Gold.'
    },
    {
      id: 'step-forecast',
      target: 'button[data-tab="tab-forecast"]',
      activeTabTarget: '#tab-forecast .forecast-hero',
      tab: 'tab-forecast',
      placement: 'bottom',
      titleKey: 'tour.step_forecast_title',
      titleDefault: 'Inferencia Cuantílica & Escenarios What-If',
      descKey: 'tour.step_forecast_desc',
      descDefault: 'Modelos predictivos Champion a 1–6 meses con cuantiles calibrados P10 (Suelo), P50 (Mediana) y P90 (Techo). Simula el impacto de variaciones en precio de búnker y desvío de transbordos.'
    },
    {
      id: 'step-simulation',
      target: 'button[data-tab="tab-simulation"]',
      activeTabTarget: '#tab-simulation .simulation-controls-card',
      tab: 'tab-simulation',
      placement: 'bottom',
      titleKey: 'tour.step_simulation_title',
      titleDefault: 'Simulación Estocástica & Riesgo Portuario',
      descKey: 'tour.step_simulation_desc',
      descDefault: 'Evaluación de resiliencia mediante Monte Carlo con 5,000 trayectorias, Teoría de Valores Extremos (EVT Gumbel) y modelos de colas M/M/c para estimar congestión de buques y calado del Canal.'
    }
  ];

  class PortOpsInteractiveTour {
    constructor() {
      this.currentStepIndex = 0;
      this.isActive = false;
      this.overlayEl = null;
      this.focalEl = null;
      this.popoverEl = null;
      this.boundKeyHandler = this.onKeyDown.bind(this);
      this.boundResizeHandler = this.reposition.bind(this);
    }

    t(key, fallback) {
      if (window.I18n && typeof window.I18n.t === 'function') {
        const val = window.I18n.t(key);
        if (val && val !== key) return val;
      }
      return fallback;
    }

    start(stepIndex = 0) {
      if (this.isActive) this.stop();
      this.isActive = true;
      this.currentStepIndex = Math.max(0, Math.min(stepIndex, TOUR_STEPS.length - 1));

      this.createTourDOM();
      document.body.classList.add('portops-tour-active');
      window.addEventListener('keydown', this.boundKeyHandler);
      window.addEventListener('resize', this.boundResizeHandler);
      window.addEventListener('scroll', this.boundResizeHandler, { passive: true });

      this.renderStep(this.currentStepIndex);
    }

    stop() {
      if (!this.isActive) return;
      this.isActive = false;
      document.body.classList.remove('portops-tour-active');
      window.removeEventListener('keydown', this.boundKeyHandler);
      window.removeEventListener('resize', this.boundResizeHandler);
      window.removeEventListener('scroll', this.boundResizeHandler);

      if (this.overlayEl && this.overlayEl.parentNode) {
        this.overlayEl.parentNode.removeChild(this.overlayEl);
      }
      this.overlayEl = null;
      this.focalEl = null;
      this.popoverEl = null;

      // Focus back to tour launcher button if present
      const launchBtn = document.getElementById('btn-start-interactive-tour');
      if (launchBtn) launchBtn.focus();
    }

    next() {
      if (this.currentStepIndex < TOUR_STEPS.length - 1) {
        this.currentStepIndex++;
        this.renderStep(this.currentStepIndex);
      } else {
        this.stop();
      }
    }

    prev() {
      if (this.currentStepIndex > 0) {
        this.currentStepIndex--;
        this.renderStep(this.currentStepIndex);
      }
    }

    onKeyDown(e) {
      if (!this.isActive) return;
      switch (e.key) {
        case 'Escape':
          e.preventDefault();
          this.stop();
          break;
        case 'ArrowRight':
        case 'Enter':
          e.preventDefault();
          this.next();
          break;
        case 'ArrowLeft':
          e.preventDefault();
          this.prev();
          break;
      }
    }

    createTourDOM() {
      const container = document.createElement('div');
      container.id = 'portops-tour-overlay-container';
      container.setAttribute('role', 'dialog');
      container.setAttribute('aria-modal', 'true');
      container.setAttribute('aria-label', 'Tour guiado interactivo de PortOps-AI');

      container.innerHTML = `
        <div class="portops-tour-backdrop"></div>
        <div class="portops-tour-focal-ring" id="portops-tour-focal-ring"></div>
        <div class="portops-tour-popover card" id="portops-tour-popover" role="document">
          <div class="portops-tour-header">
            <div class="portops-tour-step-badge">
              <span class="tour-beacon-dot"></span>
              <span id="portops-tour-step-counter">Paso 1 de 8</span>
            </div>
            <button type="button" class="portops-tour-btn-close" id="portops-tour-btn-close" aria-label="Cerrar tour (Esc)" title="Cerrar recorrido guiado">
              ✕
            </button>
          </div>
          <div class="portops-tour-progress-bar">
            <div class="portops-tour-progress-fill" id="portops-tour-progress-fill" style="width: 12.5%;"></div>
          </div>
          <div class="portops-tour-body">
            <h3 class="portops-tour-title" id="portops-tour-title"></h3>
            <p class="portops-tour-desc" id="portops-tour-desc"></p>
          </div>
          <div class="portops-tour-footer">
            <button type="button" class="btn btn-secondary portops-tour-btn-skip" id="portops-tour-btn-skip">
              ${this.t('tour.skip', 'Saltar')}
            </button>
            <div class="portops-tour-nav-buttons">
              <button type="button" class="btn btn-secondary portops-tour-btn-prev" id="portops-tour-btn-prev">
                ${this.t('tour.prev', '← Anterior')}
              </button>
              <button type="button" class="btn btn-primary portops-tour-btn-next" id="portops-tour-btn-next">
                ${this.t('tour.next', 'Siguiente →')}
              </button>
            </div>
          </div>
        </div>
      `;

      document.body.appendChild(container);
      this.overlayEl = container;
      this.focalEl = container.querySelector('#portops-tour-focal-ring');
      this.popoverEl = container.querySelector('#portops-tour-popover');

      // Hook click events
      container.querySelector('#portops-tour-btn-close').addEventListener('click', () => this.stop());
      container.querySelector('#portops-tour-btn-skip').addEventListener('click', () => this.stop());
      container.querySelector('#portops-tour-btn-prev').addEventListener('click', () => this.prev());
      container.querySelector('#portops-tour-btn-next').addEventListener('click', () => this.next());
      container.querySelector('.portops-tour-backdrop').addEventListener('click', () => this.stop());
    }

    renderStep(index) {
      const step = TOUR_STEPS[index];
      if (!step) return;

      // If step requires switching tabs, switch immediately
      if (step.tab) {
        const tabBtn = document.querySelector(`.tab-btn[data-tab="${step.tab}"]`);
        if (tabBtn && !tabBtn.classList.contains('active')) {
          tabBtn.click();
        }
      }

      // Small delay to allow tab content rendering or DOM transitions
      setTimeout(() => {
        let targetEl = null;
        if (step.activeTabTarget) {
          targetEl = document.querySelector(step.activeTabTarget);
        }
        if (!targetEl && step.target) {
          targetEl = document.querySelector(step.target);
        }
        if (!targetEl && step.targetContainer) {
          targetEl = document.querySelector(step.targetContainer);
        }

        const totalSteps = TOUR_STEPS.length;
        const currentNum = index + 1;

        // Update counter & progress
        const counterEl = document.getElementById('portops-tour-step-counter');
        if (counterEl) {
          counterEl.textContent = `${this.t('tour.step_prefix', 'Paso')} ${currentNum} ${this.t('tour.of', 'de')} ${totalSteps}`;
        }
        const progressFill = document.getElementById('portops-tour-progress-fill');
        if (progressFill) {
          progressFill.style.width = `${(currentNum / totalSteps) * 100}%`;
        }

        // Update titles and content
        const titleEl = document.getElementById('portops-tour-title');
        if (titleEl) {
          titleEl.textContent = this.t(step.titleKey, step.titleDefault);
        }
        const descEl = document.getElementById('portops-tour-desc');
        if (descEl) {
          descEl.textContent = this.t(step.descKey, step.descDefault);
        }

        // Update action buttons text
        const prevBtn = document.getElementById('portops-tour-btn-prev');
        if (prevBtn) {
          prevBtn.style.display = index === 0 ? 'none' : 'inline-flex';
          prevBtn.textContent = this.t('tour.prev', '← Anterior');
        }
        const nextBtn = document.getElementById('portops-tour-btn-next');
        if (nextBtn) {
          if (index === totalSteps - 1) {
            nextBtn.textContent = this.t('tour.finish', '✓ Finalizar');
            nextBtn.classList.add('btn-finish-highlight');
          } else {
            nextBtn.textContent = this.t('tour.next', 'Siguiente →');
            nextBtn.classList.remove('btn-finish-highlight');
          }
        }

        // Scroll and highlight target
        if (targetEl && targetEl.offsetParent !== null) {
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
          setTimeout(() => {
            this.positionAtTarget(targetEl, step.placement);
          }, 180);
        } else {
          // Fallback center position
          this.positionAtCenter();
        }
      }, 60);
    }

    positionAtTarget(targetEl, preferredPlacement = 'bottom') {
      if (!this.focalEl || !this.popoverEl) return;

      const rect = targetEl.getBoundingClientRect();
      const padding = 8;

      // Focal ring
      this.focalEl.style.display = 'block';
      this.focalEl.style.top = `${window.scrollY + rect.top - padding}px`;
      this.focalEl.style.left = `${window.scrollX + rect.left - padding}px`;
      this.focalEl.style.width = `${rect.width + padding * 2}px`;
      this.focalEl.style.height = `${rect.height + padding * 2}px`;

      // Popover coordinates calculation
      const popoverRect = this.popoverEl.getBoundingClientRect();
      const popWidth = Math.min(popoverRect.width || 420, window.innerWidth - 32);
      const popHeight = popoverRect.height || 260;

      let top = 0;
      let left = 0;

      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      // Try preferredPlacement first
      if (preferredPlacement === 'bottom' && rect.bottom + popHeight + 24 < viewportHeight) {
        top = window.scrollY + rect.bottom + 16;
        left = window.scrollX + rect.left + (rect.width / 2) - (popWidth / 2);
      } else if (rect.top - popHeight - 24 > 0) {
        top = window.scrollY + rect.top - popHeight - 16;
        left = window.scrollX + rect.left + (rect.width / 2) - (popWidth / 2);
      } else {
        // Center vertically relative to target or viewport
        top = window.scrollY + Math.max(16, rect.bottom + 16);
        left = window.scrollX + (viewportWidth / 2) - (popWidth / 2);
      }

      // Bound left to screen edges
      const minLeft = window.scrollX + 16;
      const maxLeft = window.scrollX + viewportWidth - popWidth - 16;
      left = Math.max(minLeft, Math.min(left, maxLeft));

      this.popoverEl.style.top = `${top}px`;
      this.popoverEl.style.left = `${left}px`;
      this.popoverEl.style.transform = 'none';
      this.popoverEl.focus();
    }

    positionAtCenter() {
      if (!this.focalEl || !this.popoverEl) return;
      this.focalEl.style.display = 'none';
      this.popoverEl.style.top = '50%';
      this.popoverEl.style.left = '50%';
      this.popoverEl.style.transform = 'translate(-50%, -50%)';
      this.popoverEl.focus();
    }

    reposition() {
      if (!this.isActive) return;
      this.renderStep(this.currentStepIndex);
    }
  }

  // Instantiate singleton
  const tourInstance = new PortOpsInteractiveTour();
  window.PortOpsTour = tourInstance;

  // Auto-bind to DOM elements once loaded
  function initTourBindings() {
    const launchBtn = document.getElementById('btn-start-interactive-tour');
    if (launchBtn) {
      launchBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.PortOpsTour.start(0);
      });
    }

    const heroTourBtn = document.getElementById('btn-hero-tour');
    if (heroTourBtn) {
      heroTourBtn.addEventListener('click', (e) => {
        e.preventDefault();
        window.PortOpsTour.start(0);
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTourBindings);
  } else {
    initTourBindings();
  }

})();
