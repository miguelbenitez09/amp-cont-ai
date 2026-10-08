/**
 * Panamá PortOps-AI v1.0 - Módulo RAG Aduanas, Aranceles y Validación ISO 6346
 * Desarrollado v1.0.0 Miguel Benítez | GNU GPL v3.0
 */

(function() {
  const escapeHtml = (value) => String(value ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;")
    .replace(/>/g, "&gt;").replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
  const displayValue = (value, fallback = "N/D") =>
    value === null || value === undefined || value === "" ? fallback : escapeHtml(value);
  const displayPercent = (value) => value === null || value === undefined ? "N/D" : `${escapeHtml(value)}%`;
  const displayMoney = (value) => value === null || value === undefined ? "N/D" : `$${Number(value).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD`;

  // --- 1. RAG Tariff Search ---
  window.searchCustomsTariff = async function(queryOverride) {
    const input = document.getElementById("customs-search-input");
    const container = document.getElementById("customs-results-container");
    const countBadge = document.getElementById("customs-match-count");
    const query = queryOverride !== undefined ? queryOverride : (input ? input.value.trim() : "");

    if (input && queryOverride !== undefined) {
      input.value = queryOverride;
    }

    if (container) {
      container.innerHTML = `
        <div style="text-align: center; padding: 2rem; color: var(--cyan-primary);">
          <div style="font-size: 1.5rem; margin-bottom: 0.5rem; animation: pulse 1s infinite;">⏳</div>
          <div>${window.t ? window.t("common.loading", "Consultando RAG Arancelario...") : "Consultando RAG Arancelario..."}</div>
        </div>
      `;
    }

    try {
      const url = query ? `/api/v1/customs/tariff/search?query=${encodeURIComponent(query)}` : `/api/v1/customs/tariff/search`;
      const res = await fetch(url);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const message = typeof detail === "string" ? detail : detail?.error;
        const nextStep = typeof detail === "object" ? detail?.next_step : null;
        const error = new Error(message || `HTTP ${res.status}`);
        error.nextStep = nextStep;
        error.status = res.status;
        throw error;
      }
      const items = data.items || [];

      if (countBadge) {
        countBadge.textContent = `${items.length} ${items.length === 1 ? 'partida encontrada' : 'partidas encontradas'}`;
      }

      if (!container) return;

      if (items.length === 0) {
        container.innerHTML = `
          <div style="text-align: center; padding: 2.5rem; background: rgba(255,255,255,0.02); border-radius: 8px; border: 1px dashed var(--border-color);">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
            <h4 style="color: #F8FAFC; margin-bottom: 0.4rem;">No se encontraron subpartidas para "${query}"</h4>
            <p style="color: var(--text-muted); font-size: 0.85rem; max-width: 500px; margin: 0 auto;">
              Prueba buscando por palabras clave como <em>banano, carne bovina, bunker, café, medicamentos, grúa, vehículo</em> o por código numérico como <em>0803, 8703, 0201</em>.
            </p>
          </div>
        `;
        return;
      }

      container.innerHTML = items.map((item, idx) => {
        const tr = (key, fallback) => window.t ? window.t(key, fallback) : fallback;
        const isHistorical = Boolean(item.historical_observation);
        const safeCode = escapeHtml(item.hs_code_panama);
        const safeDescription = escapeHtml(item.descripcion);
        const entities = (item.regulatory_entity_sources || (item.entidades_reguladoras || []).map(e => ({entity: e}))).map(source => {
          const label = escapeHtml(source.entity || 'N/D');
          const url = source.official_url ? escapeHtml(source.official_url) : '';
          const content = url ? `<a href="${url}" target="_blank" rel="noopener noreferrer" style="color: #00E5FF !important; text-decoration: none; font-weight: 600;">🏛️ ${label} ↗</a>` : `🏛️ ${label}`;
          const status = source.verification_status === 'official_homepage_reference' ? 'Fuente institucional de referencia; no prueba aplicabilidad legal.' : 'Fuente oficial pendiente de verificación.';
          return `<span class="badge" title="${escapeHtml(status)}" style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); font-size: 0.72rem; padding: 0.2rem 0.5rem;">${content}</span>`;
        }).join(" ");
        const evidenceVerified = item.evidence_status === 'verified_document_evidence';
        const evidenceNotice = isHistorical
          ? tr("customs.evidence_historical", "Registro histórico de observación; no representa vigencia legal actual.")
          : evidenceVerified
            ? tr("customs.evidence_verified", "Evidencia documental oficial enlazada y verificada.")
            : tr("customs.evidence_pending", "Esta ficha es una regla candidata: el procedimiento y la base legal requieren documento oficial enlazado; no prueban vigencia por sí solos.");
        const liquidationButton = isHistorical || !evidenceVerified
          ? `<button class="btn btn-secondary btn-sm" disabled title="Requiere evidencia documental ANA verificable">🔒 Liquidación bloqueada</button>`
          : `<button class="btn btn-secondary btn-sm" onclick="window.selectTariffForCalc('${safeCode}')" title="Cargar subpartida en la calculadora aduanera" style="font-size: 0.76rem; padding: 0.35rem 0.65rem;">💵 Liquidar</button>`;
        const provenanceBadge = isHistorical
          ? `<span class="badge" style="background: rgba(255, 209, 102, 0.12); color: #FFD166;">📚 Histórico INEC · clasificación observada</span>`
          : evidenceVerified
            ? `<span class="badge" style="background: rgba(0, 245, 212, 0.12); color: #00F5D4;">✅ Evidencia documental verificada</span>`
            : `<span class="badge" style="background: rgba(255, 209, 102, 0.12); color: #FFD166;">⚠️ Regla candidata · evidencia pendiente</span>`;

        const isReefer = item.requiere_reefer;
        const reeferBadge = isReefer === true
          ? `<span class="badge" style="background: rgba(0, 245, 212, 0.15); color: #00F5D4; border: 1px solid rgba(0, 245, 212, 0.4);">❄️ Requiere Reefer</span>`
          : isReefer === false
            ? `<span class="badge" style="background: rgba(255, 255, 255, 0.05); color: #94A3B8;">📦 Carga Seca</span>`
            : `<span class="badge" style="background: rgba(255, 209, 102, 0.12); color: #FFD166;">❔ Tipo de carga N/D</span>`;

        return `
          <div class="card" style="margin-bottom: 1.25rem; border-left: 4px solid #00E5FF; background: rgba(16, 26, 48, 0.6); transition: transform 0.2s ease;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem;">
              <div>
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                  <span style="font-family: var(--font-mono); font-weight: bold; font-size: 1.05rem; color: #00E5FF; letter-spacing: 0.5px;">
                    ${safeCode}
                  </span>
                  <span class="badge" style="background: rgba(255, 209, 102, 0.15); color: #FFD166; font-size: 0.72rem;">WCO HS-6: ${displayValue(item.hs_code_6)}</span>
                  ${reeferBadge}
                  ${provenanceBadge}
                  <span class="badge" style="background: rgba(148, 163, 184, 0.1); color: #94A3B8; font-size: 0.7rem;">Vigencia: ${displayValue(item.effective_from)}${item.effective_to ? ` al ${displayValue(item.effective_to)}` : ''}</span>
                </div>
                <h3 style="color: #F8FAFC; font-size: 1.05rem; margin: 0 0 4px 0;">${safeDescription}</h3>
                <div style="font-size: 0.78rem; color: var(--text-muted);">
                  <strong>Capítulo ${displayValue(item.capitulo)}:</strong> ${displayValue(item.seccion)} | <strong>Tipo:</strong> ${displayValue(item.tipo_mercancia)} | <strong>Unidad:</strong> ${displayValue(item.unidad_medida)}
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                ${liquidationButton}
                <button class="btn btn-primary btn-sm" onclick="window.copyTariffToCoT('${safeCode}', '${safeDescription.replace(/'/g, "\\'")}')" title="Consultar con Agente CoT Inteligente" style="font-size: 0.76rem; padding: 0.35rem 0.65rem; background: #00E5FF; color: #070D1E; border: none; font-weight: bold;">
                  🧠 Consultar CoT
                </button>
              </div>
            </div>

            <!-- Rates Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.6rem; margin-bottom: 0.85rem; padding: 0.65rem; background: rgba(0,0,0,0.25); border-radius: 6px;">
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Arancel DAI</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: ${item.arancel_dai_pct === 0 ? '#00F5D4' : '#FFD166'};">${displayPercent(item.arancel_dai_pct)}</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Impuesto ITBMS</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: ${item.itbms_pct === 0 ? '#00F5D4' : '#38BDF8'};">${displayPercent(item.itbms_pct)}</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Tasa DUA (Fija)</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC;">${displayValue(item.customs_declaration_fee_usd, 'N/D')} USD</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Entidades</span>
                <div style="margin-top: 2px;">${entities}</div>
              </div>
            </div>

            <!-- Details Expandable/Structured -->
            <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.82rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
              <div>
                <strong style="color: #FFD166;">📜 ${tr("customs.permits_required", "Permisos y Entidades Reguladoras:")}</strong>
                <span style="color: #E2E8F0; margin-left: 4px;">${displayValue(item.permiso_requerido)}</span>
              </div>
              <div>
                <strong style="color: #00F5D4;">📥 ${tr("customs.import_procedure", "Procedimiento de Importación:")}</strong>
                <p style="color: var(--text-muted); margin: 3px 0 0 0; line-height: 1.45;">${displayValue(item.procedimiento_importacion)}</p>
              </div>
              <div>
                <strong style="color: #38BDF8;">📤 ${tr("customs.export_procedure", "Procedimiento de Exportación / Transbordo:")}</strong>
                <p style="color: var(--text-muted); margin: 3px 0 0 0; line-height: 1.45;">${displayValue(item.procedimiento_exportacion)}</p>
              </div>
              <div style="font-size: 0.78rem; color: var(--text-dim, #CBD5E1); line-height: 1.45;">
                <strong>⚖️ ${tr("customs.legal_basis", "Base Legal y Resoluciones:")}</strong> ${displayValue(item.base_legal)}
              </div>
              <div style="font-size: 0.75rem; color: #FFD166; background: rgba(255,209,102,0.08); border-radius: 5px; padding: 0.45rem 0.55rem;">
                ${evidenceVerified ? "✅" : "⚠️"} ${evidenceNotice}
              </div>
            </div>
          </div>
        `;
      }).join("");

    } catch (err) {
      if (container) {
        container.innerHTML = `
          <div style="padding: 1.5rem; background: rgba(255,90,95,0.1); border: 1px solid rgba(255,90,95,0.3); border-radius: 8px; color: #FF5A5F;">
            <strong>Error consultando el RAG Arancelario:</strong> ${err.message}
          </div>
        `;
      }
    }
  };

  window.setCustomsPreset = function(query) {
    const input = document.getElementById("customs-search-input");
    if (input) input.value = query;
    window.searchCustomsTariff(query);
  };

  window.selectTariffForCalc = function(hsCode) {
    const calcInput = document.getElementById("calc-hs-code");
    if (calcInput) {
      calcInput.value = hsCode;
      calcInput.scrollIntoView({ behavior: "smooth", block: "center" });
      calcInput.style.boxShadow = "0 0 15px #00E5FF";
      setTimeout(() => { calcInput.style.boxShadow = ""; }, 1500);
      window.calculateCustomsLandedCost();
    }
  };

  window.copyTariffToCoT = function(hsCode, desc) {
    // Switch to CoT tab
    const cotTabBtn = document.querySelector('[data-tab="tab-cot-swarm"]');
    if (cotTabBtn) cotTabBtn.click();

    const promptInput = document.getElementById("cot-prompt-input");
    const soulSelect = document.getElementById("cot-soul-select");
    if (soulSelect) soulSelect.value = "agente_aduanero";
    if (window.updateSoulBadgeView) window.updateSoulBadgeView();

    if (promptInput) {
      promptInput.value = `Clasificar y analizar requisitos aduaneros para la subpartida ${hsCode} (${desc}). Detallar DAI, ITBMS, permisos de entidades panameñas y procedimiento de entrada portuaria.`;
      promptInput.scrollIntoView({ behavior: "smooth", block: "center" });
      promptInput.style.boxShadow = "0 0 15px #00E5FF";
      setTimeout(() => { promptInput.style.boxShadow = ""; }, 1500);
    }
  };

  // --- 2. Customs Landed Cost Calculator ---
  window.calculateCustomsLandedCost = async function() {
    const hsInput = document.getElementById("calc-hs-code");
    const cifInput = document.getElementById("calc-cif-usd");
    const resultsBox = document.getElementById("customs-calc-results");

    const hsCode = hsInput ? hsInput.value.trim() : "";
    const cifVal = cifInput ? parseFloat(cifInput.value) : NaN;

    if (!resultsBox) return;

    if (!hsCode || !Number.isFinite(cifVal) || cifVal <= 0) {
      resultsBox.innerHTML = `<div role="alert" style="padding: 0.75rem; background: rgba(255,90,95,0.1); border-radius: 6px; color: #FF5A5F; font-size: 0.8rem;">Completa un código HS y un valor CIF mayor que cero.</div>`;
      return;
    }

    resultsBox.innerHTML = `<div style="text-align: center; color: var(--cyan-primary); padding: 1rem;">Calculando liquidación fiscal...</div>`;

    try {
      const res = await fetch("/api/v1/customs/tariff/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          hs_code: hsCode,
          cif_value_usd: cifVal
        })
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = data.detail;
        const message = typeof detail === "string" ? detail : detail?.error;
        const nextStep = typeof detail === "object" ? detail?.next_step : null;
        const error = new Error(message || `HTTP ${res.status}`);
        error.nextStep = nextStep;
        error.status = res.status;
        throw error;
      }
      const c = data.liquidation || data.result || data.calculation || data;

      resultsBox.innerHTML = `
        <div style="background: rgba(10, 18, 36, 0.95); border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 8px; padding: 1.1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.6rem;">
            <div>
              <div style="font-weight: bold; color: #F8FAFC; font-size: 0.95rem;">${displayValue(c.commodity_description)}</div>
              <div style="font-size: 0.76rem; color: #00E5FF; font-family: var(--font-mono); margin-top: 2px;">HS: ${displayValue(c.hs_code || hsCode)}</div>
            </div>
            <span class="badge" style="background: rgba(0, 245, 212, 0.15); color: #00F5D4; font-size: 0.75rem; font-weight: 600;">DAI: ${displayPercent(c.dai_rate_pct)} • ITBMS: ${displayPercent(c.itbms_rate_pct)}</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.84rem; margin-bottom: 0.85rem;">
            <div style="color: var(--text-muted);">Valor CIF Declarado:</div>
            <div style="text-align: right; font-weight: bold; color: #F8FAFC;">${displayMoney(c.cif_value_usd ?? cifVal)}</div>

            <div style="color: var(--text-muted);">Arancel DAI (${displayPercent(c.dai_rate_pct)}):</div>
            <div style="text-align: right; font-weight: bold; color: #FFD166;">${displayMoney(c.dai_usd)}</div>

            <div style="color: var(--text-muted);">Impuesto ITBMS (${displayPercent(c.itbms_rate_pct)}):</div>
            <div style="text-align: right; font-weight: bold; color: #38BDF8;">${displayMoney(c.itbms_usd)}</div>

            <div style="color: var(--text-muted);">Tasa DUA Aduanas (ANA):</div>
            <div style="text-align: right; font-weight: bold; color: #F8FAFC;">${displayValue(c.customs_declaration_fee_usd, 'N/D')} USD</div>
          </div>

          <div style="background: rgba(15, 23, 42, 0.7); border-radius: 6px; padding: 0.55rem 0.75rem; margin-bottom: 0.75rem; font-size: 0.78rem; border-left: 3px solid #00E5FF;">
            <div style="color: #94A3B8;"><strong>Entidades Reguladoras:</strong> ${Array.isArray(c.regulatory_entities) && c.regulatory_entities.length ? c.regulatory_entity_sources?.map(source => source.official_url ? `<a href="${escapeHtml(source.official_url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(source.entity)} ↗</a>` : escapeHtml(source.entity)).join(', ') : 'N/D'}</div>
            <div style="color: #CBD5E1; margin-top: 3px;"><strong>Permiso Requerido:</strong> ${displayValue(c.permits_required)}</div>
          </div>

          <div style="border-top: 1px dashed var(--border-color); padding-top: 0.6rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: bold; color: #FF5A5F; font-size: 0.88rem;">Total Tributos Aduaneros:</span>
            <span style="font-weight: bold; color: #FF5A5F; font-size: 1.05rem;">${displayMoney(c.total_import_taxes_usd)}</span>
          </div>

          <div style="background: rgba(0, 245, 212, 0.1); border: 1px solid rgba(0, 245, 212, 0.3); border-radius: 6px; padding: 0.65rem 0.85rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-weight: bold; color: #00F5D4; font-size: 0.9rem; display: block;">Costo Puesto en Muelle (Landed Cost):</span>
              <span style="font-size: 0.72rem; color: #94A3B8;">Tasa efectiva: ${displayPercent(c.effective_tax_rate_pct)}</span>
            </div>
            <span style="font-weight: bold; color: #00F5D4; font-size: 1.25rem;">${displayMoney(c.total_landed_cost_usd)}</span>
          </div>
        </div>
      `;
    } catch (err) {
      resultsBox.innerHTML = `
        <div role="alert" style="padding: 0.85rem; background: rgba(255,90,95,0.1); border: 1px solid rgba(255,90,95,0.35); border-radius: 6px; color: #FF5A5F; font-size: 0.8rem;">
          <strong>${escapeHtml(err.status === 422 ? "Liquidación bloqueada" : "Error calculando liquidación")}</strong>
          <div style="margin-top: 0.35rem;">${escapeHtml(err.message)}</div>
          ${err.nextStep ? `<div style="margin-top: 0.35rem; color: #FFD166;"><strong>Siguiente paso:</strong> ${escapeHtml(err.nextStep)}</div>` : ""}
        </div>
      `;
    }
  };

  // --- 3. Container ISO 6346 Validator ---
  window.validateContainerISO6346 = async function() {
    const idInput = document.getElementById("container-id-input");
    const sizeSelect = document.getElementById("container-size-select");
    const resultsBox = document.getElementById("container-validation-results");

    const containerId = idInput ? idInput.value.trim().toUpperCase() : "";
    const sizeType = sizeSelect ? sizeSelect.value : "45G1";

    if (!resultsBox) return;
    if (!containerId) {
      resultsBox.innerHTML = `<div role="alert" style="padding: 0.75rem; background: rgba(255,90,95,0.1); border-radius: 6px; color: #FF5A5F; font-size: 0.8rem;">Completa el identificador ISO 6346 de 11 caracteres.</div>`;
      return;
    }

    resultsBox.innerHTML = `<div style="text-align: center; color: var(--cyan-primary); padding: 1rem;">Validando Módulo-11 y Manifiesto...</div>`;

    try {
      const res = await fetch("/api/v1/containers/validate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          container_id: containerId,
          size_type: sizeType
        })
      });

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const r = data.result || {};
      const v = r.validation || {};
      const spec = r.equipment_spec || {};
      const manifest = r.manifest || {};

      const isValid = v.valid === true;
      const statusBadge = isValid 
        ? `<span class="badge" style="background: rgba(0, 245, 212, 0.2); color: #00F5D4; border: 1px solid #00F5D4; font-size: 0.85rem; font-weight: bold;">✓ VÁLIDO (MOD-11 PASS)</span>`
        : `<span class="badge" style="background: rgba(255, 90, 95, 0.2); color: #FF5A5F; border: 1px solid #FF5A5F; font-size: 0.85rem; font-weight: bold;">✗ ERROR EN DÍGITO VERIFICADOR</span>`;

      resultsBox.innerHTML = `
        <div style="background: rgba(10, 18, 36, 0.95); border: 1px solid ${isValid ? 'rgba(0, 245, 212, 0.3)' : 'rgba(255, 90, 95, 0.3)'}; border-radius: 8px; padding: 1rem;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.85rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem; flex-wrap: wrap; gap: 0.5rem;">
            <div>
              <span style="font-family: var(--font-mono); font-size: 1.15rem; font-weight: bold; color: ${isValid ? '#00F5D4' : '#FF5A5F'}; letter-spacing: 1px;">
                ${v.container_id || containerId}
              </span>
              <span style="color: var(--text-muted); font-size: 0.75rem; margin-left: 6px;">ISO 6346 / BIC</span>
            </div>
            ${statusBadge}
          </div>

          <!-- Modulo-11 Breakdown -->
          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.5rem; font-size: 0.78rem; margin-bottom: 0.85rem; padding: 0.65rem; background: rgba(0,0,0,0.3); border-radius: 6px;">
            <div>
              <span style="color: var(--text-muted); display: block;">Código Propietario</span>
              <strong style="color: #00E5FF; font-size: 0.95rem;">${v.owner_code || '---'}</strong>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Identificador Cat.</span>
              <strong style="color: #FFD166; font-size: 0.95rem;">${v.category_identifier || '---'} (${v.category_description ? v.category_description.substring(0, 15) : 'Intermodal'})</strong>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Número Serial</span>
              <strong style="color: #F8FAFC; font-size: 0.95rem;">${v.serial_number || '---'}</strong>
            </div>
            <div>
              <span style="color: var(--text-muted); display: block;">Dígito Verificador</span>
              <strong style="color: ${isValid ? '#00F5D4' : '#FF5A5F'}; font-size: 0.95rem;">
                Actual: ${v.check_digit_actual !== undefined ? v.check_digit_actual : '---'} | Esperado: ${v.check_digit_expected !== undefined ? v.check_digit_expected : '---'}
              </strong>
            </div>
          </div>

          ${v.reason ? `<div style="margin-bottom: 0.75rem; font-size: 0.78rem; color: #FF5A5F; background: rgba(255,90,95,0.1); padding: 0.4rem 0.6rem; border-radius: 4px;">⚠️ ${v.reason}</div>` : ''}

          <!-- Equipment Dimensions & Manifest -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.8rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
            <div>
              <strong style="color: #00E5FF; display: block; margin-bottom: 4px;">📐 Especificaciones ISO:</strong>
              <div style="color: var(--text-muted); line-height: 1.5;">
                • Dimensiones: <strong>${displayValue(spec.length_ft)} pies (${displayValue(spec.height_ft)} ft)</strong><br>
                • Capacidad: <strong>${displayValue(r.teus)} TEUs</strong><br>
                • Tipo: <strong>${displayValue(spec.type)}</strong><br>
                • Refrigerado: <strong>${spec.is_reefer === true ? 'Sí (Reefer Activo)' : spec.is_reefer === false ? 'No (Carga Seca)' : 'N/D'}</strong>
              </div>
            </div>
            <div>
              <strong style="color: #FFD166; display: block; margin-bottom: 4px;">🚢 Manifiesto & Bahía de Estiba:</strong>
              <div style="color: var(--text-muted); line-height: 1.5;">
                • Buque: <strong>${displayValue(manifest.vessel_name)} (${displayValue(manifest.voyage_number)})</strong><br>
                • Terminal: <strong>${displayValue(manifest.terminal_name)}</strong><br>
                • Coordenada Bahía: <strong>${displayValue(manifest.bay_stowage_coordinate)}</strong><br>
                • Precinto: <strong>${displayValue(manifest.seal_number)}</strong>
              </div>
            </div>
          </div>
        </div>
      `;
    } catch (err) {
      resultsBox.innerHTML = `
        <div style="padding: 0.75rem; background: rgba(255,90,95,0.1); border-radius: 6px; color: #FF5A5F; font-size: 0.8rem;">
          Error validando contenedor: ${err.message}
        </div>
      `;
    }
  };

  window.setContainerPreset = function(id, size) {
    const idInput = document.getElementById("container-id-input");
    const sizeSelect = document.getElementById("container-size-select");
    if (idInput) idInput.value = id;
    if (sizeSelect) sizeSelect.value = size;
    window.validateContainerISO6346();
  };

  // Run initial search and validation on DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    // Initial tariff search
    setTimeout(() => {
      if (document.getElementById("customs-results-container")) {
        window.searchCustomsTariff("");
      }
    }, 600);
  });
})();
