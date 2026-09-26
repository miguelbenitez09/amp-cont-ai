/**
 * Panamá PortOps-AI v1.0 - Módulo RAG Aduanas, Aranceles y Validación ISO 6346
 * Desarrollado v1.0.0 Miguel Benítez | GNU GPL v3.0
 */

(function() {
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
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
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
        const entities = (item.entidades_reguladoras || []).map(e => 
          `<span class="badge" style="background: rgba(0, 229, 255, 0.12); color: #00E5FF; border: 1px solid rgba(0, 229, 255, 0.3); font-size: 0.72rem; padding: 0.2rem 0.5rem;">🏛️ ${e}</span>`
        ).join(" ");

        const isReefer = item.requiere_reefer;
        const reeferBadge = isReefer 
          ? `<span class="badge" style="background: rgba(0, 245, 212, 0.15); color: #00F5D4; border: 1px solid rgba(0, 245, 212, 0.4);">❄️ Requiere Reefer</span>`
          : `<span class="badge" style="background: rgba(255, 255, 255, 0.05); color: #94A3B8;">📦 Carga Seca</span>`;

        return `
          <div class="card" style="margin-bottom: 1.25rem; border-left: 4px solid #00E5FF; background: rgba(16, 26, 48, 0.6); transition: transform 0.2s ease;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 0.75rem;">
              <div>
                <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 4px;">
                  <span style="font-family: var(--font-mono); font-weight: bold; font-size: 1.05rem; color: #00E5FF; letter-spacing: 0.5px;">
                    ${item.hs_code_panama}
                  </span>
                  <span class="badge" style="background: rgba(255, 209, 102, 0.15); color: #FFD166; font-size: 0.72rem;">WCO HS-6: ${item.hs_code_6}</span>
                  ${reeferBadge}
                  <span class="badge" style="background: rgba(148, 163, 184, 0.1); color: #94A3B8; font-size: 0.7rem;">Vigencia: ${item.effective_from || '2024-01-01'} al ${item.effective_to || '2026-12-31'}</span>
                </div>
                <h3 style="color: #F8FAFC; font-size: 1.05rem; margin: 0 0 4px 0;">${item.descripcion}</h3>
                <div style="font-size: 0.78rem; color: var(--text-muted);">
                  <strong>Capítulo ${item.capitulo}:</strong> ${item.seccion} | <strong>Tipo:</strong> ${item.tipo_mercancia} | <strong>Unidad:</strong> ${item.unidad_medida}
                </div>
              </div>
              <div style="display: flex; gap: 0.5rem; align-items: center;">
                <button class="btn btn-secondary btn-sm" onclick="window.selectTariffForCalc('${item.hs_code_panama}')" title="Cargar subpartida en la calculadora aduanera" style="font-size: 0.76rem; padding: 0.35rem 0.65rem;">
                  💵 Liquidar
                </button>
                <button class="btn btn-primary btn-sm" onclick="window.copyTariffToCoT('${item.hs_code_panama}', '${item.descripcion.replace(/'/g, "\\'")}')" title="Consultar con Agente CoT Inteligente" style="font-size: 0.76rem; padding: 0.35rem 0.65rem; background: #00E5FF; color: #070D1E; border: none; font-weight: bold;">
                  🧠 Consultar CoT
                </button>
              </div>
            </div>

            <!-- Rates Grid -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.6rem; margin-bottom: 0.85rem; padding: 0.65rem; background: rgba(0,0,0,0.25); border-radius: 6px;">
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Arancel DAI</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: ${item.arancel_dai_pct === 0 ? '#00F5D4' : '#FFD166'};">${item.arancel_dai_pct}%</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Impuesto ITBMS</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: ${item.itbms_pct === 0 ? '#00F5D4' : '#38BDF8'};">${item.itbms_pct}%</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Tasa DUA (Fija)</span>
                <span style="font-size: 1.1rem; font-weight: bold; color: #F8FAFC;">$70.00 USD</span>
              </div>
              <div>
                <span style="font-size: 0.72rem; color: var(--text-muted); display: block;">Entidades</span>
                <div style="margin-top: 2px;">${entities}</div>
              </div>
            </div>

            <!-- Details Expandable/Structured -->
            <div style="display: flex; flex-direction: column; gap: 0.5rem; font-size: 0.82rem; border-top: 1px solid var(--border-color); padding-top: 0.75rem;">
              <div>
                <strong style="color: #FFD166;">📜 Permiso Institucional Requerido:</strong>
                <span style="color: #E2E8F0; margin-left: 4px;">${item.permiso_requerido || 'Inspección estándar de aduana ordinaria'}</span>
              </div>
              <div>
                <strong style="color: #00F5D4;">📥 Procedimiento Oficial de Importación:</strong>
                <p style="color: var(--text-muted); margin: 3px 0 0 0; line-height: 1.45;">${item.procedimiento_importacion || 'Trámite aduanero regular.'}</p>
              </div>
              <div>
                <strong style="color: #38BDF8;">📤 Procedimiento de Exportación / Transbordo:</strong>
                <p style="color: var(--text-muted); margin: 3px 0 0 0; line-height: 1.45;">${item.procedimiento_exportacion || 'Manifiesto de salida regular.'}</p>
              </div>
              <div style="font-size: 0.75rem; color: #64748B;">
                <strong>⚖️ Base Legal:</strong> ${item.base_legal || 'Arancel Nacional de Importación de la República de Panamá.'}
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

    const hsCode = hsInput ? hsInput.value.trim() : "0201.30.00.00.20";
    const cifVal = cifInput ? parseFloat(cifInput.value) || 10000.0 : 10000.0;

    if (!resultsBox) return;

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

      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      const c = data.liquidation || data.result || data.calculation || data;

      resultsBox.innerHTML = `
        <div style="background: rgba(10, 18, 36, 0.95); border: 1px solid rgba(0, 229, 255, 0.35); border-radius: 8px; padding: 1.1rem; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
          <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.6rem;">
            <div>
              <div style="font-weight: bold; color: #F8FAFC; font-size: 0.95rem;">${c.commodity_description || "Liquidación Oficial DUA"}</div>
              <div style="font-size: 0.76rem; color: #00E5FF; font-family: var(--font-mono); margin-top: 2px;">HS: ${c.hs_code || hsCode}</div>
            </div>
            <span class="badge" style="background: rgba(0, 245, 212, 0.15); color: #00F5D4; font-size: 0.75rem; font-weight: 600;">DAI: ${c.dai_rate_pct || 0}% • ITBMS: ${c.itbms_rate_pct || 7}%</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.84rem; margin-bottom: 0.85rem;">
            <div style="color: var(--text-muted);">Valor CIF Declarado:</div>
            <div style="text-align: right; font-weight: bold; color: #F8FAFC;">$${(c.cif_value_usd || cifVal).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD</div>

            <div style="color: var(--text-muted);">Arancel DAI (${c.dai_rate_pct || 0}%):</div>
            <div style="text-align: right; font-weight: bold; color: #FFD166;">$${(c.dai_usd || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD</div>

            <div style="color: var(--text-muted);">Impuesto ITBMS (${c.itbms_rate_pct || 7}%):</div>
            <div style="text-align: right; font-weight: bold; color: #38BDF8;">$${(c.itbms_usd || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD</div>

            <div style="color: var(--text-muted);">Tasa DUA Aduanas (ANA):</div>
            <div style="text-align: right; font-weight: bold; color: #F8FAFC;">$${(c.customs_declaration_fee_usd || 70.0).toFixed(2)} USD</div>
          </div>

          <div style="background: rgba(15, 23, 42, 0.7); border-radius: 6px; padding: 0.55rem 0.75rem; margin-bottom: 0.75rem; font-size: 0.78rem; border-left: 3px solid #00E5FF;">
            <div style="color: #94A3B8;"><strong>Entidades Reguladoras:</strong> ${(c.regulatory_entities || ['Aduanas-ANA']).join(', ')}</div>
            <div style="color: #CBD5E1; margin-top: 3px;"><strong>Permiso Requerido:</strong> ${c.permits_required || 'Trámite aduanero estándar con inspección regular'}</div>
          </div>

          <div style="border-top: 1px dashed var(--border-color); padding-top: 0.6rem; display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: bold; color: #FF5A5F; font-size: 0.88rem;">Total Tributos Aduaneros:</span>
            <span style="font-weight: bold; color: #FF5A5F; font-size: 1.05rem;">$${(c.total_import_taxes_usd || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD</span>
          </div>

          <div style="background: rgba(0, 245, 212, 0.1); border: 1px solid rgba(0, 245, 212, 0.3); border-radius: 6px; padding: 0.65rem 0.85rem; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-weight: bold; color: #00F5D4; font-size: 0.9rem; display: block;">Costo Puesto en Muelle (Landed Cost):</span>
              <span style="font-size: 0.72rem; color: #94A3B8;">Tasa efectiva: ${c.effective_tax_rate_pct || 0}%</span>
            </div>
            <span style="font-weight: bold; color: #00F5D4; font-size: 1.25rem;">$${(c.total_landed_cost_usd || 0).toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})} USD</span>
          </div>
        </div>
      `;
    } catch (err) {
      resultsBox.innerHTML = `
        <div style="padding: 0.75rem; background: rgba(255,90,95,0.1); border-radius: 6px; color: #FF5A5F; font-size: 0.8rem;">
          Error calculando liquidación: ${err.message}
        </div>
      `;
    }
  };

  // --- 3. Container ISO 6346 Validator ---
  window.validateContainerISO6346 = async function() {
    const idInput = document.getElementById("container-id-input");
    const sizeSelect = document.getElementById("container-size-select");
    const resultsBox = document.getElementById("container-validation-results");

    const containerId = idInput ? idInput.value.trim().toUpperCase() : "MSCU5281437";
    const sizeType = sizeSelect ? sizeSelect.value : "45G1";

    if (!resultsBox) return;

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
                • Dimensiones: <strong>${spec.length_ft || 40} pies (${spec.height_ft || 9.5} ft High Cube)</strong><br>
                • Capacidad: <strong>${r.teus || 2.0} TEUs</strong><br>
                • Tipo: <strong>${spec.type || 'High Cube Dry Box'}</strong><br>
                • Refrigerado: <strong>${spec.is_reefer ? 'Sí (Reefer Activo)' : 'No (Carga Seca)'}</strong>
              </div>
            </div>
            <div>
              <strong style="color: #FFD166; display: block; margin-bottom: 4px;">🚢 Manifiesto & Bahía de Estiba:</strong>
              <div style="color: var(--text-muted); line-height: 1.5;">
                • Buque: <strong>${manifest.vessel_name || 'MSC PAMELA'} (${manifest.voyage_number || '2409W'})</strong><br>
                • Terminal: <strong>${manifest.terminal_name || 'Puerto Balboa'}</strong><br>
                • Coordenada Bahía: <strong>${manifest.bay_stowage_coordinate || '010382'}</strong><br>
                • Precinto: <strong>${manifest.seal_number || 'PA-SEC-99214'}</strong>
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
      if (document.getElementById("container-validation-results")) {
        window.validateContainerISO6346();
      }
      if (document.getElementById("customs-calc-results")) {
        window.calculateCustomsLandedCost();
      }
    }, 600);
  });
})();
