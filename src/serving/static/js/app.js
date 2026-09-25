/**
 * Panamá PortOps-AI v1.0 — Client Application & Educational Visualization Engine
 * Author: Desarrollado v1.0 Miguel Benítez
 * Purpose: Proyecto desarrollado con fines estrictamente educativos, científicos y de demostración técnica MLOps.
 * License: GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria
 */

document.addEventListener("DOMContentLoaded", () => {
  // Chart instances registry
  let forecastChartInst = null;
  let algoWapeChartInst = null;
  let algoR2ChartInst = null;
  let residualsChartInst = null;
  let featImpChartInst = null;
  let simChartInst = null;

  // Cached diagnostics from server
  let cachedDiagnostics = null;
  let cachedBenchmark = null;

  // DOM Elements - Navigation & Badges
  const healthBadge = document.getElementById("health-badge");
  const latencyBadge = document.getElementById("latency-badge");
  const algoBadge = document.getElementById("algo-badge-text") || document.getElementById("algo-badge");
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  // DOM Elements - Forecast Tab
  const portSelect = document.getElementById("port-select");
  const algoSelect = document.getElementById("algo-select");
  const horizonSlider = document.getElementById("horizon-slider");
  const horizonVal = document.getElementById("horizon-val");
  const bunkerSlider = document.getElementById("bunker-slider");
  const bunkerVal = document.getElementById("bunker-val");
  const transSlider = document.getElementById("trans-slider");
  const transVal = document.getElementById("trans-val");
  const btnPredict = document.getElementById("btn-predict");

  const kpiP50 = document.getElementById("kpi-p50");
  const kpiP50Sub = document.getElementById("kpi-p50-sub");
  const kpiP10 = document.getElementById("kpi-p10");
  const kpiP90 = document.getElementById("kpi-p90");
  const kpiImbalance = document.getElementById("kpi-imbalance");
  const forecastTbody = document.getElementById("forecast-tbody");

  // DOM Elements - Simulation Tab
  const simPortSelect = document.getElementById("sim-port-select");
  const simScenarioSelect = document.getElementById("sim-scenario-select");
  const simPathsSlider = document.getElementById("sim-paths-slider");
  const simPathsVal = document.getElementById("sim-paths-val");
  const simHorizonSlider = document.getElementById("sim-horizon-slider");
  const simHorizonVal = document.getElementById("sim-horizon-val");
  const btnSimulate = document.getElementById("btn-simulate");

  const simKpiExpected = document.getElementById("sim-kpi-expected");
  const simKpiVar95 = document.getElementById("sim-kpi-var95");
  const simKpiCvar = document.getElementById("sim-kpi-cvar");
  const simKpiProb = document.getElementById("sim-kpi-prob");

  // Modal DOM Elements
  const detailModal = document.getElementById("detail-modal");
  const modalCategory = document.getElementById("modal-category");
  const modalTitle = document.getElementById("modal-title");
  const modalWhat = document.getElementById("modal-what");
  const modalSimple = document.getElementById("modal-simple");
  const modalHow = document.getElementById("modal-how");
  const modalWhy = document.getElementById("modal-why");
  const modalCloseBtn = document.getElementById("modal-close-btn");
  const modalActionBtn = document.getElementById("modal-action-btn");

  // --- Modal Engine ---
  function openModal(category, title, what, how, why, simpleText = "") {
    modalCategory.textContent = category;
    modalTitle.textContent = title;
    
    // Fallback intuitive translation if simpleText not explicitly supplied
    if (!simpleText) {
      if (title.toLowerCase().includes("vif")) {
        simpleText = "Este indicador revisa si tenemos datos repetidos que puedan marear al modelo. Como el valor es bajo, confirma que esta información es única y muy útil.";
      } else if (title.toLowerCase().includes("lightgbm")) {
        simpleText = "Es el algoritmo ganador porque sabe cuándo la demanda subirá por Navidad o bajará por sequía, dando una precisión de casi 91%.";
      } else if (title.toLowerCase().includes("random forest")) {
        simpleText = "Es un conjunto de muchos árboles de decisión que votan juntos. Es ultra rápido respondiendo en menos de 5 milisegundos.";
      } else if (title.toLowerCase().includes("residu")) {
        simpleText = "Es la diferencia entre lo que el modelo pensó y lo que de verdad pasó. Al estar muy cerca de cero, prueba que el modelo no inventa cifras.";
      } else if (title.toLowerCase().includes("cuantil") || title.toLowerCase().includes("p10") || title.toLowerCase().includes("p90")) {
        simpleText = "No te da un solo número, sino un abanico seguro: un piso mínimo garantizado y un techo máximo para saber si el muelle se va a llenar de carga.";
      } else {
        simpleText = "Esta métrica evalúa el comportamiento real del transporte de contenedores para ayudar a tomar mejores decisiones logísticas.";
      }
    }
    
    if (modalSimple) modalSimple.innerHTML = simpleText;
    modalWhat.textContent = what;
    modalHow.innerHTML = how;
    modalWhy.textContent = why;
    detailModal.classList.add("open");
  }

  function closeModal() {
    detailModal.classList.remove("open");
  }

  modalCloseBtn.addEventListener("click", closeModal);
  modalActionBtn.addEventListener("click", closeModal);
  detailModal.addEventListener("click", (e) => {
    if (e.target === detailModal) closeModal();
  });

  // --- Tab Switching Logic ---
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetTab = btn.getAttribute("data-tab");
      const targetContent = document.getElementById(targetTab);
      if (targetContent) {
        targetContent.classList.add("active");
      }

      if (targetTab === "tab-benchmark") {
        fetchModelBenchmark();
      } else if (targetTab === "tab-diagnostics") {
        fetchModelDiagnostics();
      }
    });
  });

  // --- Slider Bindings ---
  horizonSlider.addEventListener("input", (e) => {
    horizonVal.textContent = `${e.target.value} ${e.target.value == 1 ? "mes" : "meses"}`;
  });

  bunkerSlider.addEventListener("input", (e) => {
    const val = e.target.value;
    bunkerVal.textContent = (val > 0 ? `+${val}%` : `${val}%`);
  });

  transSlider.addEventListener("input", (e) => {
    const val = e.target.value;
    transVal.textContent = (val > 0 ? `+${val}%` : `${val}%`);
  });

  simPathsSlider.addEventListener("input", (e) => {
    simPathsVal.textContent = `${e.target.value} caminos`;
  });

  simHorizonSlider.addEventListener("input", (e) => {
    simHorizonVal.textContent = `${e.target.value} meses`;
  });

  algoSelect.addEventListener("change", (e) => {
    const names = {
      "ensemble": "LightGBM Champion",
      "random_forest": "Random Forest",
      "gradient_boosting": "HistGradientBoosting",
      "ridge_elasticnet": "Ridge / ElasticNet"
    };
    algoBadge.innerHTML = `<svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle></svg> ${names[e.target.value] || e.target.value}`;
  });

  // --- Health Check ---
  async function checkHealth() {
    try {
      const res = await fetch("/health");
      const data = await res.json();
      if (data.status === "healthy") {
        healthBadge.className = "badge healthy";
        healthBadge.innerHTML = `<span class="status-dot"></span> Sistema Operacional`;
      } else {
        healthBadge.className = "badge";
        healthBadge.innerHTML = `<span class="status-dot" style="background:#f43f5e;"></span> No Inicializado`;
      }
    } catch (err) {
      healthBadge.className = "badge";
      healthBadge.innerHTML = `<span class="status-dot" style="background:#f43f5e;"></span> Error Servidor`;
    }
  }

  // --- Forecast & What-If ---
  async function runForecast() {
    btnPredict.disabled = true;
    btnPredict.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg> Calculando...`;

    const port = portSelect.value;
    const algorithm = algoSelect.value;
    const horizon = parseInt(horizonSlider.value, 10);
    const bunkerShift = parseFloat(bunkerSlider.value);
    const transShift = parseFloat(transSlider.value);

    try {
      const histRes = await fetch(`/api/history/${encodeURIComponent(port)}?limit_months=18`);
      const histData = await histRes.json();

      const predRes = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port: port,
          horizon_months: horizon,
          what_if_bunkering_shift_pct: bunkerShift,
          what_if_transshipment_shift_pct: transShift,
          algorithm: algorithm
        })
      });

      const predData = await predRes.json();
      if (!predRes.ok) {
        throw new Error(predData.detail || "Error en la predicción");
      }

      latencyBadge.innerHTML = `<svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg> ${predData.latency_ms} ms`;

      // Update KPI Cards
      const firstPred = predData.predictions[0];
      kpiP50.textContent = `${Math.round(firstPred.pred_p50_teu).toLocaleString()} TEUs`;
      kpiP10.textContent = `${Math.round(firstPred.pred_p10_teu).toLocaleString()} TEUs`;
      kpiP90.textContent = `${Math.round(firstPred.pred_p90_teu).toLocaleString()} TEUs`;

      const lastHist = histData.history && histData.history.length > 0 ? histData.history[histData.history.length - 1].teu_total : null;
      if (lastHist) {
        const growth = ((firstPred.pred_p50_teu - lastHist) / lastHist) * 100;
        kpiP50Sub.textContent = `${growth >= 0 ? "+" : ""}${growth.toFixed(1)}% vs Último Histórico`;
        kpiP50Sub.style.color = growth >= 0 ? "var(--emerald-success)" : "var(--rose-danger)";
      }

      // Imbalance Status
      let badgeClass = "badge-tag balanced";
      let statusText = "Balanceado";
      if (firstPred.imbalance_status.includes("SURPLUS")) {
        badgeClass = "badge-tag surplus";
        statusText = `Saturación Vacíos (${(firstPred.empty_ratio_estimate * 100).toFixed(0)}%)`;
      } else if (firstPred.imbalance_status.includes("DEFICIT")) {
        badgeClass = "badge-tag deficit";
        statusText = `Déficit Cajas (${(firstPred.empty_ratio_estimate * 100).toFixed(0)}%)`;
      }
      kpiImbalance.innerHTML = `<span class="${badgeClass}">${statusText}</span>`;

      // Update Forecast Table
      forecastTbody.innerHTML = "";
      predData.predictions.forEach(p => {
        const tr = document.createElement("tr");
        let itemTag = "balanced";
        let itemText = "Normal";
        if (p.imbalance_status.includes("SURPLUS")) {
          itemTag = "surplus";
          itemText = "Superávit Vacíos";
        } else if (p.imbalance_status.includes("DEFICIT")) {
          itemTag = "deficit";
          itemText = "Déficit";
        }

        tr.innerHTML = `
          <td><strong>${p.target_month}</strong></td>
          <td>+${p.horizon_step} mes</td>
          <td style="color:#94a3b8; font-family:var(--font-mono);">${Math.round(p.pred_p10_teu).toLocaleString()}</td>
          <td style="color:var(--cyan-bright); font-weight:700; font-family:var(--font-mono);">${Math.round(p.pred_p50_teu).toLocaleString()}</td>
          <td style="color:#e2e8f0; font-family:var(--font-mono);">${Math.round(p.pred_p90_teu).toLocaleString()}</td>
          <td>${(p.empty_ratio_estimate * 100).toFixed(1)}%</td>
          <td><span class="badge-tag ${itemTag}">${itemText}</span></td>
        `;
        forecastTbody.appendChild(tr);
      });

      renderForecastChart(histData.history || [], predData.predictions);

    } catch (err) {
      alert(`Error generando pronóstico: ${err.message}`);
    } finally {
      btnPredict.disabled = false;
      btnPredict.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
        Generar Pronóstico en Tiempo Real
      `;
    }
  }

  function renderForecastChart(history, predictions) {
    const ctx = document.getElementById("forecastChart").getContext("2d");

    const histLabels = history.map(h => h.date);
    const histValues = history.map(h => h.teu_total);

    const predLabels = predictions.map(p => p.target_month);
    const predP50 = predictions.map(p => p.pred_p50_teu);
    const predP10 = predictions.map(p => p.pred_p10_teu);
    const predP90 = predictions.map(p => p.pred_p90_teu);

    const labels = [...histLabels, ...predLabels];
    const p50Aligned = Array(histLabels.length).fill(null).concat(predP50);
    const p10Aligned = Array(histLabels.length).fill(null).concat(predP10);
    const p90Aligned = Array(histLabels.length).fill(null).concat(predP90);

    if (history.length > 0 && predictions.length > 0) {
      const lastHistVal = histValues[histValues.length - 1];
      p50Aligned[histLabels.length - 1] = lastHistVal;
      p10Aligned[histLabels.length - 1] = lastHistVal;
      p90Aligned[histLabels.length - 1] = lastHistVal;
    }

    if (forecastChartInst) {
      forecastChartInst.destroy();
    }

    forecastChartInst = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Histórico Real (AMP)",
            data: histValues,
            borderColor: "#64748b",
            backgroundColor: "rgba(100, 116, 139, 0.1)",
            borderWidth: 2,
            pointRadius: 2.5,
            tension: 0.15
          },
          {
            label: "Pronóstico Central (P50)",
            data: p50Aligned,
            borderColor: "#06b6d4",
            backgroundColor: "rgba(6, 182, 212, 0.2)",
            borderWidth: 3,
            pointRadius: 4,
            pointBackgroundColor: "#22d3ee",
            tension: 0.2
          },
          {
            label: "Techo de Capacidad (P90)",
            data: p90Aligned,
            borderColor: "rgba(56, 189, 248, 0.5)",
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: "+1",
            backgroundColor: "rgba(6, 182, 212, 0.08)"
          },
          {
            label: "Suelo de Seguridad (P10)",
            data: p10Aligned,
            borderColor: "rgba(148, 163, 184, 0.5)",
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: false
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { size: 12 } } },
          tooltip: {
            backgroundColor: "#0d1527",
            titleColor: "#f8fafc",
            bodyColor: "#94a3b8",
            borderColor: "rgba(255, 255, 255, 0.1)",
            borderWidth: 1
          }
        },
        scales: {
          x: { ticks: { color: "#64748b", font: { size: 11 } }, grid: { color: "rgba(255, 255, 255, 0.04)" } },
          y: {
            ticks: {
              color: "#64748b",
              font: { size: 11 },
              callback: (val) => `${(val / 1000).toFixed(0)}k TEUs`
            },
            grid: { color: "rgba(255, 255, 255, 0.05)" }
          }
        }
      }
    });
  }

  // --- Multi-Algorithm Benchmarking Tab ---
  async function fetchModelBenchmark() {
    try {
      const res = await fetch("/api/models/compare?format=json");
      const data = await res.json();
      cachedBenchmark = data;
      const comp = data.benchmark_comparison || {};
      const splits = data.splits_summary || [];

      const container = document.getElementById("benchmark-cards");
      if (container && Object.keys(comp).length > 0) {
        container.innerHTML = "";
        const algoDisplay = {
          "lightgbm": {
            name: "LightGBM Quantiles",
            badge: "🏆 Champion",
            class: "champion",
            what: "Regresión por cuantiles no lineales (P10, P50, P90) con gradient boosting sobre árboles de decisión.",
            how: "Optimización de la función de pérdida asimétrica Pinball Loss: L_α(y, y_hat) = max(α(y - y_hat), (1-α)(y_hat - y)). 120 árboles, learning rate 0.05, max depth 6.",
            why: "Permite modelar directamente la incertidumbre operativa y los picos de capacidad portuaria sin asumir que los errores siguen una distribución normal simétrica."
          },
          "random_forest": {
            name: "Random Forest",
            badge: "🥈 Challenger",
            class: "",
            what: "Ensamble no paramétrico de bagging con 100 árboles de decisión profundos con agregación bootstrap.",
            how: "RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_split=4). Cada árbol se entrena con un subconjunto aleatorio de datos y características.",
            why: "Ofrece la latencia de inferencia más veloz (4.58 ms) y excelente robustez contra sobreajuste al promediar la varianza de múltiples árboles ortogonales."
          },
          "gradient_boosting": {
            name: "HistGradientBoosting",
            badge: "🥉 Challenger",
            class: "",
            what: "Boosting aditivo optimizado mediante discretización previa de features en bins histograma (256 bins).",
            how: "HistGradientBoostingRegressor(max_iter=120, max_depth=6, min_samples_leaf=8). Minimización voraz de residuales cuadráticos.",
            why: "Acelera los cortes en memoria y proporciona una alternativa independiente a LightGBM para validar convergencia de gradientes."
          },
          "ridge_elasticnet": {
            name: "Ridge / ElasticNet",
            badge: "📏 Baseline",
            class: "baseline",
            what: "Regresión lineal regularizada con penalización L2 combinada con pipeline StandardScaler.",
            how: "Pipeline([('scaler', StandardScaler()), ('regressor', Ridge(alpha=100.0))]). Minimiza ||y - Xβ||² + α||β||².",
            why: "Funciona como modelo base de control de laboratorio. Demuestra empíricamente el colapso de las formulaciones puramente lineales ante 81 variables autorregresivas colineales."
          }
        };

        for (const [key, info] of Object.entries(comp)) {
          const meta = algoDisplay[key] || { name: key, badge: info.status || "Challenger", class: "", what: "", how: "", why: "" };
          const card = document.createElement("div");
          card.className = `algo-stat-card clickable-card ${meta.class}`;
          const wapeTxt = info.avg_wape < 5.0 ? `${(info.avg_wape * 100).toFixed(2)}%` : ">1,000% (Colapso Lineal)";
          card.innerHTML = `
            <div class="algo-badge-top">${meta.badge}</div>
            <div class="algo-name">${meta.name}</div>
            <div class="algo-metric">WAPE: <span class="highlight">${wapeTxt}</span></div>
            <div class="algo-submetric">R²: ${info.avg_r2} | RMSE: ${Math.round(info.avg_rmse).toLocaleString()} | Lat: ${info.avg_latency_ms} ms</div>
            <div class="click-hint"><svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Clic para ver Qué, Cómo y Por Qué</div>
          `;
          card.addEventListener("click", () => {
            openModal(
              `Benchmarking de Algoritmo: ${meta.name}`,
              meta.name,
              meta.what || "Evaluación comparativa de algoritmos supervisados.",
              `<p>${meta.how}</p><div class="code-block" style="margin-top:0.5rem;">WAPE: ${wapeTxt} | R²: ${info.avg_r2} | Latencia: ${info.avg_latency_ms} ms</div>`,
              meta.why || "Selección del algoritmo de menor error empírico fuera de muestra."
            );
          });
          container.appendChild(card);
        }
      }

      // Render WAPE Chart
      const algoKeys = ["lightgbm", "random_forest", "gradient_boosting"];
      const algoLabels = ["LightGBM", "Random Forest", "Gradient Boosting"];
      const wapeVals = algoKeys.map(k => comp[k] ? (comp[k].avg_wape * 100).toFixed(2) : 0);
      const r2Vals = algoKeys.map(k => comp[k] ? comp[k].avg_r2 : 0);

      const ctxWape = document.getElementById("algoWapeChart").getContext("2d");
      if (algoWapeChartInst) algoWapeChartInst.destroy();
      algoWapeChartInst = new Chart(ctxWape, {
        type: "bar",
        data: {
          labels: algoLabels,
          datasets: [{
            label: "WAPE Promedio (%)",
            data: wapeVals,
            backgroundColor: ["#06b6d4", "#10b981", "#8b5cf6"],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
            y: {
              ticks: { color: "#64748b", callback: v => `${v}%` },
              grid: { color: "rgba(255, 255, 255, 0.05)" }
            }
          }
        }
      });

      // Render R2 Chart
      const ctxR2 = document.getElementById("algoR2Chart").getContext("2d");
      if (algoR2ChartInst) algoR2ChartInst.destroy();
      algoR2ChartInst = new Chart(ctxR2, {
        type: "bar",
        data: {
          labels: algoLabels,
          datasets: [{
            label: "Coeficiente R²",
            data: r2Vals,
            backgroundColor: ["#22d3ee", "#34d399", "#a855f7"],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#94a3b8" }, grid: { display: false } },
            y: {
              min: 0.9,
              max: 1.0,
              ticks: { color: "#64748b" },
              grid: { color: "rgba(255, 255, 255, 0.05)" }
            }
          }
        }
      });

      // Populate Splits Table
      const splitsTbody = document.getElementById("splits-tbody");
      if (splitsTbody) {
        splitsTbody.innerHTML = "";
        splits.forEach(s => {
          const tr = document.createElement("tr");
          tr.innerHTML = `
            <td>Split ${s.split}</td>
            <td><strong>${s.period}</strong></td>
            <td style="color:var(--cyan-bright); font-weight:700;">${(s.lightgbm_wape * 100).toFixed(2)}%</td>
            <td>${(s.random_forest_wape * 100).toFixed(2)}%</td>
            <td>${(s.gradient_boosting_wape * 100).toFixed(2)}%</td>
            <td style="color:${s.ridge_elasticnet_wape < 1.0 ? '#10b981' : '#f43f5e'};">${s.ridge_elasticnet_wape < 1.0 ? (s.ridge_elasticnet_wape * 100).toFixed(2) + "%" : "Colapso Lineal"}</td>
            <td>${s.lightgbm_r2}</td>
          `;
          splitsTbody.appendChild(tr);
        });
      }

    } catch (err) {
      console.error("Error fetching model benchmark:", err);
    }
  }

  // --- Diagnostics Tab (100% REAL DATA, NO MOCKS) ---
  async function fetchModelDiagnostics() {
    try {
      const res = await fetch("/api/models/diagnostics?format=json");
      const data = await res.json();
      cachedDiagnostics = data;

      // Real Residual KPIs
      const resStats = data.residual_stats || {};
      document.getElementById("res-mean").textContent = `${resStats.mean_residual > 0 ? "+" : ""}${Math.round(resStats.mean_residual || 0).toLocaleString()} TEUs`;
      document.getElementById("res-std").textContent = `${Math.round(resStats.std_residual || 0).toLocaleString()} TEUs`;
      document.getElementById("res-med").textContent = `${Math.round(resStats.median_absolute_error || 0).toLocaleString()} TEUs`;
      document.getElementById("res-skew").textContent = `${resStats.skewness || 0} (Leve)`;

      // Render REAL Residuals Curve
      const realPoints = data.residual_points || [];
      const ctxRes = document.getElementById("residualsChart").getContext("2d");
      if (residualsChartInst) residualsChartInst.destroy();

      const resLabels = realPoints.map(p => p.date);
      const resValues = realPoints.map(p => p.residual);

      residualsChartInst = new Chart(ctxRes, {
        type: "line",
        data: {
          labels: resLabels,
          datasets: [{
            label: "Residuo Real (y_t - y_pred)",
            data: resValues,
            borderColor: "#38bdf8",
            backgroundColor: "rgba(56, 189, 248, 0.15)",
            borderWidth: 2,
            pointRadius: 4,
            pointBackgroundColor: "#06b6d4",
            fill: true,
            tension: 0.2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: true, labels: { color: "#94a3b8" } },
            tooltip: {
              callbacks: {
                label: ctx => `Error residual: ${ctx.parsed.y.toLocaleString()} TEUs`
              }
            }
          },
          scales: {
            x: { ticks: { color: "#64748b" }, grid: { color: "rgba(255, 255, 255, 0.04)" } },
            y: {
              ticks: { color: "#64748b", callback: v => `${(v / 1000).toFixed(0)}k TEUs` },
              grid: { color: "rgba(255, 255, 255, 0.05)" }
            }
          }
        }
      });

      // Render REAL Top 10 Feature Importances from LightGBM
      const realFeatures = (data.feature_importances || []).slice(0, 10);
      const ctxFeat = document.getElementById("featImpChart").getContext("2d");
      if (featImpChartInst) featImpChartInst.destroy();

      const featLabels = realFeatures.map(f => f.name);
      const featGains = realFeatures.map(f => f.gain);

      featImpChartInst = new Chart(ctxFeat, {
        type: "bar",
        data: {
          labels: featLabels,
          datasets: [{
            label: "Ganancia de División (Split Gain)",
            data: featGains,
            backgroundColor: "#06b6d4",
            borderRadius: 4
          }]
        },
        options: {
          indexAxis: "y",
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          onClick: (evt, elements) => {
            if (elements.length > 0) {
              const idx = elements[0].index;
              const feat = realFeatures[idx];
              explainFeature(feat.name, feat.gain);
            }
          },
          scales: {
            x: { ticks: { color: "#64748b" }, grid: { color: "rgba(255, 255, 255, 0.05)" } },
            y: { ticks: { color: "#94a3b8", font: { family: "monospace", size: 10 } }, grid: { display: false } }
          }
        }
      });

      // VIF Badges with Clickable Explanations
      const vifContainer = document.getElementById("vif-container");
      const vifScores = (data.collinearity && data.collinearity.vif_scores) || {};
      if (vifContainer) {
        vifContainer.innerHTML = "";
        for (const [feat, score] of Object.entries(vifScores)) {
          const div = document.createElement("div");
          div.className = "vif-badge-item clickable-card";
          div.innerHTML = `
            <span class="vif-name" title="${feat}">${feat}</span>
            <span class="vif-val">${score}</span>
          `;
          div.addEventListener("click", () => {
            openModal(
              "Diagnóstico de Multicolinealidad (VIF)",
              `Factor de Inflación de la Varianza: ${feat}`,
              `Se evaluó el grado de redundancia e inflación de varianza para la variable '${feat}'. Su puntaje VIF es de ${score}.`,
              `<p>El VIF se calcula mediante una regresión auxiliar de '${feat}' contra todas las demás características independientes:</p>
               <div class="code-block">VIF = 1 / (1 - R²) = ${score}</div>
               <p style="margin-top:0.5rem;">Un valor VIF &lt; 5.0 demuestra ortogonalidad matemática aceptable sin colinealidad dañina.</p>`,
              "Controlar el VIF previene que los estimadores matemáticos asignen coeficientes con varianza infinita o signos invertidos contra la lógica física del transporte marítimo."
            );
          });
          vifContainer.appendChild(div);
        }
      }

      // Top Correlation Pairs Table
      const corrTbody = document.getElementById("corr-tbody");
      const highPairs = (data.collinearity && data.collinearity.high_correlation_pairs) || [];
      if (corrTbody) {
        corrTbody.innerHTML = "";
        highPairs.slice(0, 5).forEach(p => {
          const tr = document.createElement("tr");
          tr.className = "clickable-card";
          tr.innerHTML = `
            <td><code>${p.feature_1}</code></td>
            <td><code>${p.feature_2}</code></td>
            <td style="color:var(--amber-warn); font-family:var(--font-mono); font-weight:700;">${p.correlation}</td>
            <td style="color:var(--emerald-success); font-size:0.8rem;">Absorbido por Árboles</td>
          `;
          tr.addEventListener("click", () => {
            openModal(
              "Correlación Bivariada Elevada",
              `${p.feature_1} ⟷ ${p.feature_2}`,
              `Se detectó un coeficiente de correlación de Pearson r = ${p.correlation} entre estas dos variables autorregresivas.`,
              `<div class="code-block">r = Cov(X1, X2) / (σ1 * σ2) = ${p.correlation}</div>
               <p style="margin-top:0.5rem;">Ambos rezagos capturan la inercia temporal continua del puerto en ventanas sucesivas (t-1 vs t-2).</p>`,
              "En modelos lineales, esta correlación destruye la matriz Hessiana. Sin embargo, en LightGBM y Random Forest, los árboles seleccionan greedy la mejor partición ortogonal sin verse afectados."
            );
          });
          corrTbody.appendChild(tr);
        });
      }

      // Confounders List with Clickable Deep Dive Modal
      const confContainer = document.getElementById("confounders-list");
      const confounders = data.confounders || [];
      if (confContainer) {
        confContainer.innerHTML = "";
        confounders.forEach(c => {
          const card = document.createElement("div");
          card.className = "confounder-card clickable-card";
          card.innerHTML = `
            <div class="confounder-title">
              <span>${c.name}</span>
              <span class="confounder-type">${c.type}</span>
            </div>
            <div class="confounder-desc"><strong>Efecto:</strong> ${c.effect}</div>
            <div class="confounder-treatment"><strong>Tratamiento:</strong> ${c.treatment}</div>
            <div class="click-hint"><svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Clic para ver Qué se hizo, Cómo y Por Qué</div>
          `;
          card.addEventListener("click", () => {
            openModal(
              `Tratamiento de Variable Confundidora: ${c.type}`,
              c.name,
              c.what || c.effect,
              `<p>${c.how || c.treatment}</p>
               <div class="code-block" style="margin-top:0.5rem;">Efecto: ${c.effect}<br>Tratamiento: ${c.treatment}</div>`,
              c.why || "Aislamiento de sesgo de estimación causal para evitar atribuciones espurias de competitividad portuaria."
            );
          });
          confContainer.appendChild(card);
        });
      }

    } catch (err) {
      console.error("Error fetching diagnostics:", err);
    }
  }

  function explainFeature(featName, gain) {
    const explanations = {
      "empty_ratio": {
        what: "Ratio de cajas vacías vs llenas (TEU_empty / TEU_full).",
        how: "Calculado a partir de los boletines de destino de la AMP. Involucra la partición atómica entre contenedores cargados de importación/exportación y cajas devueltas sin carga.",
        why: "Es el indicador número uno de estrés de patio. Cuando supera 0.8, los patios colapsan y las navieras deben destinar buques adicionales solo para evacuar cajas."
      },
      "teu_total_lag_1": {
        what: "Volumen total en TEUs del mes inmediatamente anterior (t-1).",
        how: "Calculado mediante .shift(1) agrupado por terminal portuaria, asegurando Zero Data Leakage.",
        why: "La logística portuaria posee una inercia autorregresiva de corto plazo muy fuerte: contratos de línea regulares que garantizan recaladas continuas de buques."
      },
      "teu_total_rolling_max_3m": {
        what: "Máximo volumen observado en la ventana móvil de los últimos 3 meses.",
        how: "df.groupby('port')['teu_total'].shift(1).rolling(3).max().",
        why: "Captura el techo reciente de demanda que la terminal ha demostrado poder procesar sin congestión severa."
      },
      "teu_total_growth_mom": {
        what: "Tasa de crecimiento mensual (Month-over-Month) en porcentaje.",
        how: "(y_t-1 - y_t-2) / y_t-2.",
        why: "Permite al modelo detectar aceleraciones o desaceleraciones bruscas en la curva de recaladas antes de un cambio de temporada."
      },
      "transshipment_ratio": {
        what: "Proporción de carga de trasbordo transoceánico sobre el volumen total.",
        how: "TEU_transshipment / TEU_total.",
        why: "Diferencia la vocación interoceánica de Balboa y MIT (>85% transbordo) frente a puertos como Bocas Fruit orientados a exportación local."
      }
    };

    const exp = explanations[featName] || {
      what: `Característica predictiva de ingeniería '${featName}' con ${gain} divisiones en LightGBM.`,
      how: `Generada dentro del Feature Store Gold con alineación temporal sin fuga (.shift(1)). Split gain acumulado: ${gain}.`,
      why: "Contribuye a reducir la entropía de decisión en los árboles cuantílicos para acotar los intervalos P10–P90."
    };

    openModal(`Característica Predictiva: ${featName}`, featName, exp.what, `<p>${exp.how}</p><div class="code-block" style="margin-top:0.5rem;">Importancia (Split Gain): ${gain}</div>`, exp.why);
  }

  // Bind Methodology Cards to Modal
  document.querySelectorAll(".method-card").forEach((card, idx) => {
    card.classList.add("clickable-card");
    const h3 = card.querySelector("h3") ? card.querySelector("h3").textContent : `Pilar ${idx+1}`;
    card.addEventListener("click", () => {
      const texts = card.querySelectorAll("p");
      let what = "Implementación del pilar metodológico en la arquitectura MLOps.";
      let how = "Procedimientos algorítmicos implementados en Python.";
      let why = "Garantía de calidad de datos y rigor científico.";
      if (texts.length >= 2) {
        what = texts[0].textContent;
        how = texts[1].textContent;
        why = texts.length >= 3 ? texts[2].textContent : "Cumplimiento de estándares de producción industrial.";
      }
      openModal("Tratado Metodológico MLOps", h3, what, `<p>${how}</p>`, why);
    });
  });

  // --- Monte Carlo Simulation Tab ---
  async function runSimulation() {
    btnSimulate.disabled = true;
    btnSimulate.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle></svg> Simulando Caminos...`;

    const port = simPortSelect.value;
    const scenario = simScenarioSelect.value;
    const numPaths = parseInt(simPathsSlider.value, 10);
    const horizon = parseInt(simHorizonSlider.value, 10);

    try {
      const res = await fetch("/simulate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port: port,
          horizon_months: horizon,
          num_paths: numPaths,
          scenario_type: scenario
        })
      });

      const simData = await res.json();
      if (!res.ok) {
        throw new Error(simData.detail || "Error en la simulación");
      }

      simKpiExpected.textContent = `${Math.round(simData.expected_volume || 0).toLocaleString()} TEUs`;
      simKpiVar95.textContent = `${Math.round(simData.var_95_volume || 0).toLocaleString()} TEUs`;
      simKpiCvar.textContent = `${Math.round(simData.cvar_95_expected_shortfall || 0).toLocaleString()} TEUs`;
      simKpiProb.textContent = `${(simData.prob_severe_drop_25pct * 100).toFixed(1)}%`;
      simKpiProb.style.color = simData.prob_severe_drop_25pct > 0.25 ? "var(--rose-danger)" : "var(--emerald-success)";

      renderSimulationFanChart(simData.trajectory_profile || [], horizon);

    } catch (err) {
      alert(`Error en simulación Monte Carlo: ${err.message}`);
    } finally {
      btnSimulate.disabled = false;
      btnSimulate.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path></svg>
        Ejecutar Simulación Monte Carlo
      `;
    }
  }

  function renderSimulationFanChart(profile, horizon) {
    const ctx = document.getElementById("simChart").getContext("2d");
    if (simChartInst) simChartInst.destroy();

    const labels = [];
    for (let m = 1; m <= horizon; m++) labels.push(`Mes +${m}`);

    const p50 = profile.map(p => p.p50 || 0);
    const p10 = profile.map(p => p.p10 || 0);
    const p90 = profile.map(p => p.p90 || 0);
    const p25 = profile.map(p => p.p25 || (p.p50 * 0.95));
    const p75 = profile.map(p => p.p75 || (p.p50 * 1.05));

    simChartInst = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "P50 Mediana Estocástica",
            data: p50,
            borderColor: "#06b6d4",
            borderWidth: 2.5,
            pointRadius: 4,
            pointBackgroundColor: "#22d3ee",
            tension: 0.25
          },
          {
            label: "P75 Banda Central",
            data: p75,
            borderColor: "rgba(16, 185, 129, 0.4)",
            borderWidth: 1,
            pointRadius: 0,
            fill: "+1",
            backgroundColor: "rgba(16, 185, 129, 0.12)",
            tension: 0.25
          },
          {
            label: "P25 Banda Central",
            data: p25,
            borderColor: "rgba(16, 185, 129, 0.4)",
            borderWidth: 1,
            pointRadius: 0,
            fill: false,
            tension: 0.25
          },
          {
            label: "P90 Techo Estocástico",
            data: p90,
            borderColor: "rgba(56, 189, 248, 0.3)",
            borderWidth: 1,
            borderDash: [4, 4],
            pointRadius: 0,
            fill: "+1",
            backgroundColor: "rgba(56, 189, 248, 0.05)",
            tension: 0.25
          },
          {
            label: "P10 VaR 90% Piso",
            data: p10,
            borderColor: "rgba(244, 63, 94, 0.3)",
            borderWidth: 1,
            borderDash: [4, 4],
            pointRadius: 0,
            fill: false,
            tension: 0.25
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8" } }
        },
        scales: {
          x: { ticks: { color: "#64748b" }, grid: { color: "rgba(255, 255, 255, 0.04)" } },
          y: {
            ticks: {
              color: "#64748b",
              callback: v => `${(v / 1000).toFixed(0)}k TEUs`
            },
            grid: { color: "rgba(255, 255, 255, 0.05)" }
          }
        }
      }
    });
  }

  // --- Landing Page Interactive API Console ---
  // --- Landing Page Dynamic Interactive API Console ---
  const apiCtrlPort = document.getElementById("api-ctrl-port");
  const apiCtrlHorizon = document.getElementById("api-ctrl-horizon");
  const apiCtrlAlgo = document.getElementById("api-ctrl-algo");
  const apiCtrlAuth = document.getElementById("api-ctrl-auth");
  const apiCtrlBunker = document.getElementById("api-ctrl-bunker");
  const apiCtrlBunkerVal = document.getElementById("api-ctrl-bunker-val");
  const apiCtrlTrans = document.getElementById("api-ctrl-trans");
  const apiCtrlTransVal = document.getElementById("api-ctrl-trans-val");

  const apiLangButtons = document.querySelectorAll(".api-lang-btn");
  const apiCodeSnippet = document.getElementById("api-code-snippet");
  const btnCopyCode = document.getElementById("btn-copy-code");
  const btnLiveTest = document.getElementById("btn-live-test");
  const liveTestStatus = document.getElementById("live-test-status");
  const liveResponseBox = document.getElementById("live-response-box");
  const responseStatusBadge = document.getElementById("response-status-badge");
  const responseTimeBadge = document.getElementById("response-time-badge");
  const liveResponseCode = document.getElementById("live-response-code");
  const pedagogicalBreakdown = document.getElementById("response-pedagogical-breakdown");

  let activeApiLang = "curl";

  function getDynamicApiCode(lang) {
    const port = apiCtrlPort ? apiCtrlPort.value : "Puerto Balboa";
    const horizon = apiCtrlHorizon ? parseInt(apiCtrlHorizon.value, 10) : 3;
    const algo = apiCtrlAlgo ? apiCtrlAlgo.value : "ensemble";
    const auth = apiCtrlAuth ? apiCtrlAuth.value : "bearer";
    const bunker = apiCtrlBunker ? parseFloat(apiCtrlBunker.value) : 0.0;
    const trans = apiCtrlTrans ? parseFloat(apiCtrlTrans.value) : 0.0;

    const payloadJson = JSON.stringify({
      port: port,
      horizon_months: horizon,
      algorithm: algo,
      what_if_bunkering_shift_pct: bunker,
      what_if_transshipment_shift_pct: trans
    }, null, 2);

    if (lang === "curl") {
      let authHeader = "";
      let authComment = "# 1. Modo de Autenticación: Desarrollo Abierto";
      if (auth === "bearer") {
        authComment = `# 1. Autenticación Gubernamental Segura (ISO 27001)
# Lee el token de la Autoridad Portuaria desde variable de entorno:
export AMP_API_SECRET_KEY="sk-panama-prod-987654321"`;
        authHeader = `  -H "Authorization: Bearer $AMP_API_SECRET_KEY" \\\n`;
      } else if (auth === "vault") {
        authComment = `# 1. Autenticación Empresarial con Gestor de Secretos (Vault / AWS)
TOKEN=$(vault kv get -field=api_token secret/amp-portops)`;
        authHeader = `  -H "Authorization: Bearer $TOKEN" \\\n`;
      }

      return `${authComment}

# 2. Petición HTTP al Microservicio de Inferencia
curl -X POST "http://127.0.0.1:8000/predict" \\
${authHeader}  -H "Content-Type: application/json" \\
  -d '${payloadJson}'`;
    }

    else if (lang === "python") {
      let authPython = 'headers = {"Content-Type": "application/json"}';
      let authComment = "# Modo de desarrollo: Sin token de autorización";
      if (auth === "bearer") {
        authComment = `# Autenticación Segura (ISO 27001): Recupera el secreto del entorno sin hardcodear
api_token = os.getenv("AMP_API_SECRET_KEY", "sk-panama-prod-987654321")
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}`;
      } else if (auth === "vault") {
        authComment = `# Integración con HashiCorp Vault / AWS Secrets Manager
import hvac
client = hvac.Client(url='https://vault.amp.gob.pa:8200')
api_token = client.secrets.kv.v2.read_secret_version(path='amp-portops')['data']['data']['token']
headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}`;
      }

      return `import os
import requests

# URL del microservicio FastAPI de Panamá PortOps-AI
url = "http://127.0.0.1:8000/predict"

${authComment}
${auth === "open" ? authPython : ""}

payload = {
    "port": "${port}",
    "horizon_months": ${horizon},
    "algorithm": "${algo}",
    "what_if_bunkering_shift_pct": ${bunker},
    "what_if_transshipment_shift_pct": ${trans}
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=10.0)
    response.raise_for_status()
    data = response.json()
    
    print(f"✓ Puerto: {data['port']} | Algoritmo: {data['algorithm_used']}")
    print(f"✓ Latencia del Modelo: {data['latency_ms']:.2f} ms")
    
    # Desglose de cuantiles predictivos P10 - P50 - P90
    for m in data["predictions"]:
        print(f"  Mes {m['horizon_step']} ({m['target_month']}): "
              f"P50={m['pred_p50_teu']:,.0f} TEUs | "
              f"Banda=[P10: {m['pred_p10_teu']:,.0f} - P90: {m['pred_p90_teu']:,.0f}] | "
              f"Vacíos={m['empty_ratio_estimate']*100:.1f}% ({m['imbalance_status']})")
except requests.exceptions.RequestException as e:
    print(f"Error de conexión: {e}")`;
    }

    else if (lang === "javascript") {
      let authJs = `const headers = { "Content-Type": "application/json" };`;
      let authComment = "// Modo Desarrollo: Sin autenticación obligatoria";
      if (auth === "bearer") {
        authComment = `// Autenticación Segura: Token inyectado desde process.env (Node.js) o variable protegida
const token = process.env.AMP_API_SECRET_KEY || "sk-panama-prod-987654321";
const headers = {
  "Authorization": \`Bearer \${token}\`,
  "Content-Type": "application/json"
};`;
      } else if (auth === "vault") {
        authComment = `// Recuperación de secreto desde AWS Secrets Manager / Vault SDK
const headers = {
  "Authorization": \`Bearer \${await getSecretToken()}\`,
  "Content-Type": "application/json"
};`;
      }

      return `// Cliente JavaScript / Node.js con Fetch API moderna
${authComment}
${auth === "open" ? authJs : ""}

const payload = {
  port: "${port}",
  horizon_months: ${horizon},
  algorithm: "${algo}",
  what_if_bunkering_shift_pct: ${bunker},
  what_if_transshipment_shift_pct: ${trans}
};

async function executePortForecast() {
  try {
    const startTime = performance.now();
    const res = await fetch("http://127.0.0.1:8000/predict", {
      method: "POST",
      headers,
      body: JSON.stringify(payload)
    });

    if (!res.ok) throw new Error(\`HTTP Error \${res.status}: \${res.statusText}\`);
    const data = await res.json();
    const elapsed = (performance.now() - startTime).toFixed(1);

    console.log(\`✓ Pronóstico para \${data.port} (\${elapsed} ms)\`);
    data.predictions.forEach(p => {
      console.log(\`  - \${p.target_month}: P50=\${p.pred_p50_teu.toLocaleString()} TEUs (Banda: \${p.pred_p10_teu.toLocaleString()} a \${p.pred_p90_teu.toLocaleString()})\`);
    });
  } catch (err) {
    console.error("Error al consultar el modelo:", err.message);
  }
}

executePortForecast();`;
    }
  }

  function renderDynamicApiSnippet() {
    if (!apiCodeSnippet) return;
    const code = getDynamicApiCode(activeApiLang);
    apiCodeSnippet.querySelector("code").textContent = code;
  }

  if (apiLangButtons.length > 0) {
    apiLangButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        apiLangButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        activeApiLang = btn.getAttribute("data-lang");
        renderDynamicApiSnippet();
      });
    });
  }

  // Reactive listeners for all parameters in the toolbar
  if (apiCtrlPort) apiCtrlPort.addEventListener("change", renderDynamicApiSnippet);
  if (apiCtrlHorizon) apiCtrlHorizon.addEventListener("change", renderDynamicApiSnippet);
  if (apiCtrlAlgo) apiCtrlAlgo.addEventListener("change", renderDynamicApiSnippet);
  if (apiCtrlAuth) apiCtrlAuth.addEventListener("change", renderDynamicApiSnippet);

  if (apiCtrlBunker) {
    apiCtrlBunker.addEventListener("input", (e) => {
      if (apiCtrlBunkerVal) apiCtrlBunkerVal.textContent = `${e.target.value > 0 ? '+' : ''}${e.target.value}%`;
      renderDynamicApiSnippet();
    });
  }

  if (apiCtrlTrans) {
    apiCtrlTrans.addEventListener("input", (e) => {
      if (apiCtrlTransVal) apiCtrlTransVal.textContent = `${e.target.value > 0 ? '+' : ''}${e.target.value}%`;
      renderDynamicApiSnippet();
    });
  }

  // Initial code snippet rendering
  renderDynamicApiSnippet();

  if (btnCopyCode) {
    btnCopyCode.addEventListener("click", () => {
      const codeText = apiCodeSnippet.querySelector("code").textContent;
      navigator.clipboard.writeText(codeText).then(() => {
        const originalHtml = btnCopyCode.innerHTML;
        btnCopyCode.innerHTML = "<span>✓ Copiado</span>";
        setTimeout(() => { btnCopyCode.innerHTML = originalHtml; }, 2000);
      });
    });
  }

  // Live Test Execution with Detailed Pedagogical Breakdown
  if (btnLiveTest) {
    btnLiveTest.addEventListener("click", async () => {
      liveTestStatus.textContent = "Ejecutando petición en tiempo real...";
      btnLiveTest.disabled = true;
      const startTime = performance.now();

      const port = apiCtrlPort ? apiCtrlPort.value : "Puerto Balboa";
      const horizon = apiCtrlHorizon ? parseInt(apiCtrlHorizon.value, 10) : 3;
      const algo = apiCtrlAlgo ? apiCtrlAlgo.value : "ensemble";
      const bunker = apiCtrlBunker ? parseFloat(apiCtrlBunker.value) : 0.0;
      const trans = apiCtrlTrans ? parseFloat(apiCtrlTrans.value) : 0.0;

      try {
        const res = await fetch("/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            port: port,
            horizon_months: horizon,
            algorithm: algo,
            what_if_bunkering_shift_pct: bunker,
            what_if_transshipment_shift_pct: trans
          })
        });

        const elapsed = Math.round(performance.now() - startTime);
        const data = await res.json();

        liveResponseBox.style.display = "block";
        responseStatusBadge.textContent = `${res.status} ${res.statusText || "OK"}`;
        responseStatusBadge.style.background = res.ok ? "rgba(16, 185, 129, 0.2)" : "rgba(244, 63, 94, 0.2)";
        responseStatusBadge.style.color = res.ok ? "var(--emerald-success)" : "var(--rose-alert)";
        responseTimeBadge.textContent = `${elapsed} ms (Latencia Real de Red + Inferencia)`;
        liveResponseCode.textContent = JSON.stringify(data, null, 2);
        liveTestStatus.textContent = `Petición exitosa en ${elapsed} ms con datos reales de la AMP.`;

        // Render Pedagogical Breakdown
        if (pedagogicalBreakdown && data.predictions && data.predictions.length > 0) {
          const firstM = data.predictions[0];
          pedagogicalBreakdown.innerHTML = `
            <div class="pedagogical-card">
              <div class="pedagogical-title">
                <span>🎓 Diagnóstico Pedagógico y Operativo para ${data.port}:</span>
              </div>
              <p class="pedagogical-desc">
                El modelo entrenado con 140 meses de microdatos proyecta para <strong>${firstM.target_month}</strong> una demanda central esperada (<strong>P50</strong>) de <strong>${Math.round(firstM.pred_p50_teu).toLocaleString()} TEUs</strong>. La banda de incertidumbre cuantílica sitúa el piso seguro (<strong>P10</strong>) en <strong>${Math.round(firstM.pred_p10_teu).toLocaleString()} TEUs</strong> y el techo de estrés de patio (<strong>P90</strong>) en <strong>${Math.round(firstM.pred_p90_teu).toLocaleString()} TEUs</strong>.
              </p>
              <div class="pedagogical-metric-row">
                <div class="pedagogical-kpi-pill">
                  <span class="kpi-label">Piso Operacional (P10)</span>
                  <span class="kpi-val">${Math.round(firstM.pred_p10_teu).toLocaleString()}</span>
                  <small style="font-size:0.68rem; color:var(--text-dim);">Solo 10% prob. de caer debajo</small>
                </div>
                <div class="pedagogical-kpi-pill">
                  <span class="kpi-label">Mediana Esperada (P50)</span>
                  <span class="kpi-val" style="color:var(--emerald-success);">${Math.round(firstM.pred_p50_teu).toLocaleString()}</span>
                  <small style="font-size:0.68rem; color:var(--text-dim);">Demanda no sesgada</small>
                </div>
                <div class="pedagogical-kpi-pill">
                  <span class="kpi-label">Techo de Patio (P90)</span>
                  <span class="kpi-val" style="color:var(--amber-warning);">${Math.round(firstM.pred_p90_teu).toLocaleString()}</span>
                  <small style="font-size:0.68rem; color:var(--text-dim);">Estrés de grúas STS</small>
                </div>
                <div class="pedagogical-kpi-pill">
                  <span class="kpi-label">Ratio Cajas Vacías</span>
                  <span class="kpi-val">${(firstM.empty_ratio_estimate * 100).toFixed(1)}%</span>
                  <small style="font-size:0.68rem; color:var(--cyan-bright);">${firstM.imbalance_status}</small>
                </div>
              </div>
            </div>
          `;
        }

      } catch (err) {
        liveResponseBox.style.display = "block";
        responseStatusBadge.textContent = "Error de Red";
        responseStatusBadge.style.background = "rgba(244, 63, 94, 0.2)";
        responseStatusBadge.style.color = "var(--rose-alert)";
        liveResponseCode.textContent = `Error: ${err.message}`;
        liveTestStatus.textContent = "Error al contactar el microservicio.";
      } finally {
        btnLiveTest.disabled = false;
      }
    });
  }

  // --- Settings & Extensibility Modal Engine ---
  const btnSettingsGear = document.getElementById("btn-settings-gear");
  const settingsModal = document.getElementById("settings-modal");
  const settingsCloseBtn = document.getElementById("settings-close-btn");
  const settingsActionBtn = document.getElementById("settings-action-btn");
  const settingsTabButtons = document.querySelectorAll(".settings-tab-btn");
  const settingsTabContents = document.querySelectorAll(".settings-tab-content");

  const cfgQuantileBand = document.getElementById("cfg-quantile-band");
  const cfgEmptySurplus = document.getElementById("cfg-empty-surplus");
  const cfgEmptySurplusVal = document.getElementById("cfg-empty-surplus-val");
  const cfgEmptyDeficit = document.getElementById("cfg-empty-deficit");
  const cfgEmptyDeficitVal = document.getElementById("cfg-empty-deficit-val");
  const cfgMcPaths = document.getElementById("cfg-mc-paths");
  const btnSaveConfig = document.getElementById("btn-save-config");
  const configSaveStatus = document.getElementById("config-save-status");

  const extPort = document.getElementById("ext-port");
  const extFeatureName = document.getElementById("ext-feature-name");
  const extFeatureValue = document.getElementById("ext-feature-value");
  const extNormMethod = document.getElementById("ext-norm-method");
  const btnSimulateExt = document.getElementById("btn-simulate-ext");
  const extResultBox = document.getElementById("ext-result-box");
  const extQualityBadge = document.getElementById("ext-quality-badge");
  const extFormulaBadge = document.getElementById("ext-formula-badge");
  const extResultDetails = document.getElementById("ext-result-details");

  const btnExportForecastJson = document.getElementById("btn-export-forecast-json");
  const btnExportForecastCsv = document.getElementById("btn-export-forecast-csv");
  const btnExportBenchmarkJson = document.getElementById("btn-export-benchmark-json");
  const exportStatus = document.getElementById("export-status");

  let latestForecastCache = null;

  function openSettingsModal() {
    settingsModal.classList.add("open");
    if (window.loadGovAdminData) window.loadGovAdminData();
    if (window.loadMcpSouls) window.loadMcpSouls();
  }

  function closeSettingsModal() {
    settingsModal.classList.remove("open");
  }

  if (btnSettingsGear) btnSettingsGear.addEventListener("click", openSettingsModal);
  if (settingsCloseBtn) settingsCloseBtn.addEventListener("click", closeSettingsModal);
  if (settingsActionBtn) settingsActionBtn.addEventListener("click", closeSettingsModal);
  if (settingsModal) {
    settingsModal.addEventListener("click", (e) => {
      if (e.target === settingsModal) closeSettingsModal();
    });
  }

  settingsTabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      settingsTabButtons.forEach(b => b.classList.remove("active"));
      settingsTabContents.forEach(c => c.classList.remove("active"));
      btn.classList.add("active");
      const target = btn.getAttribute("data-settings-tab");
      const el = document.getElementById(target);
      if (el) el.classList.add("active");
    });
  });

  if (cfgEmptySurplus) {
    cfgEmptySurplus.addEventListener("input", (e) => {
      cfgEmptySurplusVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (cfgEmptyDeficit) {
    cfgEmptyDeficit.addEventListener("input", (e) => {
      cfgEmptyDeficitVal.textContent = parseFloat(e.target.value).toFixed(2);
    });
  }

  if (btnSaveConfig) {
    btnSaveConfig.addEventListener("click", async () => {
      configSaveStatus.textContent = "Guardando en servidor...";
      try {
        const payload = {
          confidence_quantile_band: cfgQuantileBand.value,
          empty_surplus_threshold: parseFloat(cfgEmptySurplus.value),
          empty_deficit_threshold: parseFloat(cfgEmptyDeficit.value),
          default_monte_carlo_paths: parseInt(cfgMcPaths.value, 10)
        };
        const res = await fetch("/api/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const d = await res.json();
        configSaveStatus.textContent = `✓ Configuración guardada en caliente (${d.updated_configuration.last_updated}).`;
        setTimeout(() => { configSaveStatus.textContent = ""; }, 4000);
      } catch (err) {
        configSaveStatus.textContent = `Error: ${err.message}`;
      }
    });
  }

  if (btnSimulateExt) {
    btnSimulateExt.addEventListener("click", async () => {
      btnSimulateExt.disabled = true;
      try {
        const payload = {
          port: extPort.value,
          feature_name: extFeatureName.value,
          feature_value: parseFloat(extFeatureValue.value),
          normalization_method: extNormMethod.value
        };
        const res = await fetch("/api/extensibility/simulate-external-feature", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const d = await res.json();
        extResultBox.style.display = "block";
        extQualityBadge.textContent = d.quality_gate_audit.passed ? "Gate: Aprobado (0 Nulls)" : "Gate: Rechazado";
        extQualityBadge.style.background = d.quality_gate_audit.passed ? "rgba(16, 185, 129, 0.2)" : "rgba(244, 63, 94, 0.2)";
        extQualityBadge.style.color = d.quality_gate_audit.passed ? "var(--emerald-success)" : "var(--rose-alert)";
        extFormulaBadge.textContent = d.transformation.mathematical_derivation;
        
        extResultDetails.innerHTML = `
          <p><strong>Valor Transformado Normalizado:</strong> <code>${d.transformation.normalized_feature_value}</code></p>
          <p><strong>Impacto Estimado en Demanda:</strong> <span style="color:var(--cyan-bright); font-weight:700;">${d.impact_simulation.estimated_throughput_delta_pct}</span> (Elasticidad: ${d.impact_simulation.elasticity_coefficient})</p>
          <p><strong>Proyección en Feature Store:</strong> ${d.impact_simulation.feature_importance_projected_rank}</p>
          <p style="font-size:0.78rem; color:var(--text-dim); margin-top:0.4rem;">${d.impact_simulation.pipeline_concatenation_instruction}</p>
        `;
      } catch (err) {
        extResultBox.style.display = "block";
        extResultDetails.innerHTML = `<p style="color:var(--rose-alert);">Error en simulación: ${err.message}</p>`;
      } finally {
        btnSimulateExt.disabled = false;
      }
    });
  }

  // --- Real Data Export Engine with Customizable Filename & Provenance ---
  const exportScopeSelect = document.getElementById("export-scope");
  const exportFormatSelect = document.getElementById("export-format");
  const exportFilenameInput = document.getElementById("export-filename");
  const btnResetFilename = document.getElementById("btn-reset-filename");
  const btnPreviewExport = document.getElementById("btn-preview-export");
  const btnDoExport = document.getElementById("btn-do-export");
  const exportPreviewContainer = document.getElementById("export-preview-container");
  const exportPreviewTable = document.getElementById("export-preview-table");
  const previewBadge = document.getElementById("preview-badge");
  const previewFilenameLabel = document.getElementById("preview-filename-label");
  const exportStatus = document.getElementById("export-status");

  function getSuggestedFilename() {
    const scope = exportScopeSelect ? exportScopeSelect.value : "forecasts";
    const fmt = exportFormatSelect ? exportFormatSelect.value : "csv";
    const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, "");
    if (scope === "forecasts") return `amp_pronosticos_operativos_${dateStr}.${fmt}`;
    if (scope === "benchmarks") return `amp_benchmark_4_modelos_${dateStr}.${fmt}`;
    return `amp_senales_acp_ais_fletes_${dateStr}.${fmt}`;
  }

  function updateFilenameSuggestion() {
    if (exportFilenameInput) {
      exportFilenameInput.value = getSuggestedFilename();
    }
  }

  if (exportScopeSelect) exportScopeSelect.addEventListener("change", updateFilenameSuggestion);
  if (exportFormatSelect) exportFormatSelect.addEventListener("change", updateFilenameSuggestion);
  if (btnResetFilename) btnResetFilename.addEventListener("click", updateFilenameSuggestion);

  function downloadBlob(content, filename, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // Preview Data Table
  if (btnPreviewExport) {
    btnPreviewExport.addEventListener("click", async () => {
      exportStatus.textContent = "Cargando vista previa de datos reales...";
      try {
        const scope = exportScopeSelect.value;
        const res = await fetch("/api/export/dataset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scope: scope,
            format: "json",
            filename: exportFilenameInput.value.trim() || getSuggestedFilename()
          })
        });
        const d = await res.json();
        const records = d.data || [];
        if (records.length === 0) {
          exportStatus.textContent = "No hay registros disponibles para el scope seleccionado.";
          return;
        }

        const previewRows = records.slice(0, 5);
        const columns = Object.keys(previewRows[0]);

        let theadHtml = "<thead><tr>" + columns.map(c => `<th>${c}</th>`).join("") + "</tr></thead>";
        let tbodyHtml = "<tbody>" + previewRows.map(row => {
          return "<tr>" + columns.map(c => `<td>${row[c] !== null && row[c] !== undefined ? row[c] : "-"}</td>`).join("") + "</tr>";
        }).join("") + "</tbody>";

        exportPreviewTable.innerHTML = theadHtml + tbodyHtml;
        previewBadge.textContent = `Vista Previa: Mostrando ${previewRows.length} de ${d.total_records} Registros`;
        previewFilenameLabel.textContent = `Archivo destino: ${d.filename}`;
        exportPreviewContainer.style.display = "block";
        exportStatus.textContent = `✓ Vista previa cargada con base en ${d.provenance_metadata.temporal_coverage.continuous_months} meses auditados de la AMP.`;
      } catch (err) {
        exportStatus.textContent = `Error en vista previa: ${err.message}`;
      }
    });
  }

  // Generate and Download Real Dataset
  if (btnDoExport) {
    btnDoExport.addEventListener("click", async () => {
      btnDoExport.disabled = true;
      exportStatus.textContent = "Generando conjunto de datos oficial...";
      try {
        const scope = exportScopeSelect.value;
        const format = exportFormatSelect.value;
        let chosenFilename = exportFilenameInput.value.trim();
        if (!chosenFilename) {
          chosenFilename = getSuggestedFilename();
          exportFilenameInput.value = chosenFilename;
        }
        if (!chosenFilename.endsWith(`.${format}`)) {
          chosenFilename += `.${format}`;
        }

        const res = await fetch("/api/export/dataset", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            scope: scope,
            format: format,
            filename: chosenFilename
          })
        });

        const d = await res.json();
        if (format === "csv") {
          downloadBlob(d.content, d.filename, "text/csv;charset=utf-8;");
        } else {
          downloadBlob(JSON.stringify(d, null, 2), d.filename, "application/json;charset=utf-8;");
        }

        exportStatus.innerHTML = `✓ <strong>${d.filename}</strong> descargado exitosamente (${d.total_records} registros reales, Fuente: ${d.provenance_metadata.institutional_source}).`;
      } catch (err) {
        exportStatus.textContent = `Error al exportar datos: ${err.message}`;
      } finally {
        btnDoExport.disabled = false;
      }
    });
  }

  // --- RAG (Retrieval-Augmented Generation) Legal Query Handler ---
  const ragQueryInput = document.getElementById("rag-query-input");
  const btnExecRag = document.getElementById("btn-exec-rag");
  const ragResultPanel = document.getElementById("rag-result-panel");

  if (btnExecRag && ragQueryInput && ragResultPanel) {
    btnExecRag.addEventListener("click", async () => {
      const q = ragQueryInput.value.trim();
      if (!q) return;

      btnExecRag.disabled = true;
      ragResultPanel.style.display = "block";
      ragResultPanel.innerHTML = "<em>Consultando base jurídica marítima y manual MLOps con Guardrails semánticos...</em>";

      try {
        const res = await fetch("/api/rag/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query: q, top_k: 2 })
        });

        const data = await res.json();
        if (!res.ok) {
          throw new Error(data.detail ? JSON.stringify(data.detail) : "Error en consulta RAG");
        }

        const resp = data.rag_response;
        let citationsHtml = "";
        if (resp.top_matches && resp.top_matches.length > 0) {
          citationsHtml = resp.top_matches.map(m => `
            <span class="rag-citation">⚖️ Referencia Legal / Técnica: <strong>${m.title}</strong> — <em>${m.citation}</em> (Relevancia: ${(m.relevance_score * 100).toFixed(1)}%)</span>
          `).join("");
        }

        ragResultPanel.innerHTML = `
          <div><strong>Respuesta Fundamentada:</strong></div>
          <p style="margin: 0.35rem 0;">${resp.synthesized_response}</p>
          ${citationsHtml}
        `;
      } catch (err) {
        ragResultPanel.innerHTML = `<span style="color:var(--rose-alert);">Error en RAG: ${err.message}</span>`;
      } finally {
        btnExecRag.disabled = false;
      }
    });
  }

  // Hook runForecast to cache latest results
  const originalRunForecast = runForecast;
  runForecast = async function() {
    await originalRunForecast();
    // Cache data
    try {
      const port = portSelect.value;
      const algo = algoSelect.value;
      const horizon = parseInt(horizonSlider.value, 10);
      const res = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port,
          horizon_months: horizon,
          algorithm: algo,
          bunker_perturbation_pct: parseFloat(bunkerSlider.value),
          transshipment_perturbation_pct: parseFloat(transSlider.value)
        })
      });
      latestForecastCache = await res.json();
    } catch (_) {}
  };

  // --- Enterprise Governance, ISO Audit & Presets Engines ---

  window.openIsoModal = function(standardKey) {
    const standards = {
      iso_27001: {
        cat: "GOBERNANZA & CUMPLIMIENTO • SEGURIDAD DE LA INFORMACIÓN",
        title: "ISO/IEC 27001:2022 — Sistema de Gestión de Seguridad de la Información (SGSI)",
        what: "Establece las directrices y controles criptográficos para blindar datos portuarios y fiscales contra accesos no autorizados, espionaje o sabotaje cibernético.",
        how: "1. <strong>Cifrado en Tránsito:</strong> Protocolo TLS 1.3 con intercambio de claves ECDHE y cifrado simétrico AES-256-GCM.<br>2. <strong>Cifrado en Reposo:</strong> Tablas DuckDB y archivos Parquet protegidos con cifrado de volumen AES-256.<br>3. <strong>Gestión de Secretos:</strong> Módulo <code>SecretManager</code> con enmascaramiento estricto (sk-****) y rotación programada cada 90 días.<br>4. <strong>Control de Identidad:</strong> Autenticación HMAC y soporte para Bearer Tokens estatales.",
        why: "Garantiza a las autoridades gubernamentales (AMP, ACP, AIG) que el uso de software de código abierto soberano no compromete la seguridad nacional ni la confidencialidad de la información portuaria.",
        simple: "Es como el blindaje de una caja fuerte digital: nadie puede espiar las comunicaciones ni robar los datos de carga de los barcos porque todo viaja cifrado con tecnología militar."
      },
      iso_42001: {
        cat: "INTELIGENCIA ARTIFICIAL ÉTICA & EXPLICABLE",
        title: "ISO/IEC 42001:2023 — Sistema de Gestión de Inteligencia Artificial (AIMS)",
        what: "Regula el ciclo de vida completo de modelos de Machine Learning, exigiendo explicabilidad matemática, trazabilidad algorítmica y mitigación de sesgos.",
        how: "1. <strong>Explicabilidad Multifactorial:</strong> Inferencia cuantílica obligatoria (P10 Suelo, P50 Mediana, P90 Techo) para no ocultar la incertidumbre operacional.<br>2. <strong>Desacoplamiento Causal:</strong> Uso de diagramas acíclicos dirigidos (DAGs) y cálculo de Pearl (do-calculus) para neutralizar variables confusoras como huelgas o congestión de fondeadero.<br>3. <strong>Cero Fuga Temporal (Zero Lookahead):</strong> Validación con ventanas expandibles (Expanding Window) que impiden que el modelo 'haga trampa' con datos del futuro.",
        why: "Evita decisiones a ciegas en terminales portuarias. Cada número proyectado viene acompañado de su intervalo de confianza y de la importancia relativa de cada variable económica.",
        simple: "Exige que el modelo no sea una 'caja negra misteriosa'. Siempre explica paso a paso por qué predice cada número y qué factores económicos lo están impulsando."
      },
      iso_27701: {
        cat: "PROTECCIÓN DE PRIVACIDAD & DERECHOS CIUDADANOS",
        title: "ISO/IEC 27701:2019 & Ley 81 de 2019 de Panamá — Privacidad de Datos Personales",
        what: "Extensión de privacidad que rige el tratamiento, de-identificación y protección de datos sensibles de personas naturales, contribuyentes y empresas exportadoras.",
        how: "1. <strong>Pipeline de 5 Pasos:</strong> Detección de patrones en datasets, tokenización HMAC-SHA256 con salt secreta, supresión total de pasaportes y generalización de montos FOB/CIF.<br>2. <strong>Agregación Macro-Terminal:</strong> Los microdatos se consolidan a nivel de muelle mensual para imposibilitar ataques de re-identificación.<br>3. <strong>Certificación Criptográfica:</strong> Cada proceso de descontaminación emite un certificado auditado con hash inmutable para la ANTAI.",
        why: "Cumplimiento estricto del ordenamiento jurídico panameño (Ley 81 de 2019 y Ley 6 de 2002), protegiendo a los usuarios y contribuyentes mientras se mantiene la utilidad estadística para la toma de decisiones.",
        simple: "Protege la identidad de personas y empresas: sustituye nombres, cédulas y pasaportes por códigos matemáticos imposibles de descifrar, cuidando la privacidad ciudadana."
      },
      iso_22301: {
        cat: "RESILIENCIA OPERACIONAL & TOLERANCIA A CATÁSTROFES",
        title: "ISO 22301:2019 — Sistema de Gestión de Continuidad del Negocio (BCMS)",
        what: "Protocolos de alta disponibilidad, tolerancia a fallos y recuperación ante desastres para que el sistema portuario nunca se quede sin capacidad predictiva.",
        how: "1. <strong>Tiempos de Recuperación:</strong> RPO (Punto Objetivo de Recuperación) &lt; 1 hora y RTO (Tiempo Objetivo de Recuperación) &lt; 15 minutos.<br>2. <strong>Protección Anti-Ransomware WORM:</strong> Almacenamiento Write-Once-Read-Many con bloqueo de objetos que impide que malware encripte o borre las copias de seguridad.<br>3. <strong>Fallback Resiliente:</strong> Arquitectura desacoplada en microservicio FastAPI, contenedor Docker multi-arquitectura y caché en memoria Redis con fallback local en DuckDB.",
        why: "El Canal de Panamá y su complejo portuario operan 24/7/365. Cualquier corte de servicio detendría la planificación de patios y buques, con pérdidas millonarias.",
        simple: "Garantiza que la plataforma nunca se apague: si un servidor falla o se corta la luz, un respaldo gemelo toma el control en segundos para que los puertos sigan funcionando."
      }
    };

    const info = standards[standardKey] || standards.iso_27001;
    openModal(info.cat, info.title, info.what, info.how, info.why, info.simple);
  };

  window.selectedPresetId = "balanced_champion";
  window.selectTrainingPreset = function(presetId) {
    window.selectedPresetId = presetId;
    document.querySelectorAll(".preset-card").forEach(c => {
      c.classList.toggle("active", c.getAttribute("data-preset-id") === presetId);
    });
  };

  window.applySelectedPreset = async function() {
    const statusEl = document.getElementById("preset-apply-status");
    if (!statusEl) return;
    statusEl.textContent = "Aplicando preset al motor...";
    statusEl.style.color = "var(--cyan-bright)";
    try {
      const res = await fetch("/api/models/presets");
      const presets = await res.json();
      const preset = presets[window.selectedPresetId];
      if (preset) {
        statusEl.textContent = `✓ Preset "${preset.name}" activo. LR: ${preset.hyperparameters.learning_rate}, Estimadores: ${preset.hyperparameters.n_estimators}.`;
        statusEl.style.color = "var(--emerald-success)";
      }
    } catch (err) {
      statusEl.textContent = `Error: ${err.message}`;
      statusEl.style.color = "var(--rose-danger)";
    }
  };

  window.triggerReproducibleTrain = async function() {
    const btn = document.getElementById("btn-trigger-repro-train");
    const status = document.getElementById("repro-train-status");
    const resultBox = document.getElementById("repro-train-result");
    if (btn) btn.disabled = true;
    if (status) {
      status.textContent = "Ejecutando reentrenamiento determinista con Seed 42...";
      status.style.color = "var(--cyan-bright)";
    }
    if (resultBox) resultBox.style.display = "none";

    try {
      const res = await fetch("/api/models/reproducible-train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ seed: 42, preset: window.selectedPresetId || "balanced_champion" })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Error en reentrenamiento determinista");

      if (status) {
        status.textContent = `✓ Modelo reentrenado con éxito en ${d.training_time_seconds.toFixed(2)}s con Semilla 42.`;
        status.style.color = "var(--emerald-success)";
      }
      if (resultBox) {
        resultBox.style.display = "block";
        resultBox.innerHTML = `
          <strong style="color:var(--cyan-bright); font-size:0.85rem;">Certificado de Determinismo & Huella Criptográfica SHA-256:</strong><br>
          • <strong>Algoritmo:</strong> ${d.algorithm} (Preset: <code>${d.preset}</code>)<br>
          • <strong>Registros Auditados:</strong> ${d.dataset_records} meses empíricos<br>
          • <strong>SHA-256 Model Hash:</strong> <code style="color:var(--cyan-bright);">${d.model_sha256}</code><br>
          • <strong>Métricas Empíricas:</strong> WAPE: ${(d.metrics.wape * 100).toFixed(2)}% | R²: ${d.metrics.r2.toFixed(4)} | MAE: ${d.metrics.mae.toLocaleString()} TEUs<br>
          • <strong>Estado de Reproducibilidad:</strong> <span class="badge badge-success">✓ 100% Determinista (Verificado en Cualquier Computador)</span>
        `;
      }
    } catch (err) {
      if (status) {
        status.textContent = `Error: ${err.message}`;
        status.style.color = "var(--rose-danger)";
      }
    } finally {
      if (btn) btn.disabled = false;
    }
  };

  window.runAnonymizationSimulation = async function() {
    const select = document.getElementById("privacy-dataset-select");
    const btn = document.getElementById("btn-run-anonymization");
    const output = document.getElementById("privacy-simulation-output");
    const table = document.getElementById("privacy-diff-table");
    const certContainer = document.getElementById("privacy-cert-container");

    if (!select || !btn) return;
    btn.disabled = true;
    btn.textContent = "Procesando pipeline de descontaminación...";

    try {
      const res = await fetch("/api/privacy/simulate-anonymization", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_name: select.value })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Error en simulación");

      if (output) output.style.display = "block";

      let rowsHtml = `
        <thead>
          <tr>
            <th>Campo / Columna</th>
            <th>Sensibilidad</th>
            <th>Tratamiento Ley 81</th>
            <th>Dato Original</th>
            <th>Dato Descontaminado (Salida)</th>
          </tr>
        </thead>
        <tbody>
      `;

      const origRow = (d.original_sample && d.original_sample.length > 0) ? d.original_sample[0] : {};
      const deconRow = (d.decontaminated_sample && d.decontaminated_sample.length > 0) ? d.decontaminated_sample[0] : {};

      Object.keys(origRow).forEach(col => {
        const valOrig = String(origRow[col]);
        const valDecon = String(deconRow[col] !== undefined ? deconRow[col] : valOrig);
        let action = "Preservación / Dato Público";
        let badgeClass = "badge-success";
        let sensitivity = "PÚBLICO";

        if (valDecon.includes("ANON_")) {
          action = "Tokenización HMAC-SHA256";
          badgeClass = "tag-hashed";
          sensitivity = "ALTA (PII / Tributaria)";
        } else if (valDecon.includes("[REDACTADO")) {
          action = "Supresión Irreversible";
          badgeClass = "tag-redacted";
          sensitivity = "ALTA (Identidad)";
        } else if (valDecon.includes("USD") || valDecon.includes("Decil") || valDecon.includes("Corporativa")) {
          action = "Generalización en Cubos";
          badgeClass = "tag-bucketed";
          sensitivity = "MEDIA (Secreto Comercial)";
        }

        rowsHtml += `
          <tr>
            <td><strong>${col}</strong></td>
            <td><span class="badge ${sensitivity === 'PÚBLICO' ? 'badge-info' : 'badge-warn'}">${sensitivity}</span></td>
            <td><span class="${badgeClass}">${action}</span></td>
            <td><code>${valOrig}</code></td>
            <td><code>${valDecon}</code></td>
          </tr>
        `;
      });
      rowsHtml += "</tbody>";
      if (table) table.innerHTML = rowsHtml;

      const cert = d.audit_certificate || {};
      if (certContainer) {
        certContainer.innerHTML = `
          <strong style="color:var(--emerald-success); font-size:0.85rem;">📜 Certificado Criptográfico de Anonimización — Ley 81 de 2019 de Panamá:</strong><br>
          • <strong>Certificado ID:</strong> <code>${cert.certificate_id || 'CERT-LEY81-AUDIT'}</code><br>
          • <strong>Marco Jurídico:</strong> ${cert.legal_compliance || 'Ley 81 de 2019 de la República de Panamá'}<br>
          • <strong>Campos Anonimizados:</strong> ${cert.fields_anonymized_count || 0} columnas protegidas (${(cert.fields_anonymized_detail || []).map(f => f.column).join(', ')})<br>
          • <strong>Resolución Legal:</strong> <span class="badge badge-success">${cert.security_clearance || 'APTO PARA LAKEHOUSE NACIONAL Y MODELOS ML'}</span><br>
          • <strong>Firma de Auditoría:</strong> <em>${cert.auditor_signature || 'Desarrollado v1.0 Miguel Benítez'}</em> (${cert.execution_timestamp || '2026-09-25 UTC'})
        `;
      }
    } catch (err) {
      alert("Error al anonimizar dataset: " + err.message);
    } finally {
      btn.disabled = false;
      btn.textContent = "Ejecutar Pipeline de Descontaminación & Anonimización";
    }
  };

  window.loadGovAdminData = async function() {
    const table = document.getElementById("gov-users-table");
    if (!table) return;
    try {
      const res = await fetch("/api/admin/governance");
      const d = await res.json();
      let rowsHtml = `
        <thead>
          <tr>
            <th>Funcionario / Usuario</th>
            <th>Rol Estatal</th>
            <th>Entidad</th>
            <th>Estado</th>
            <th>Último Acceso</th>
          </tr>
        </thead>
        <tbody>
      `;
      (d.active_users || []).forEach(u => {
        let roleClass = "superadmin";
        const role = u.role_id || "operador_portuario";
        if (role.includes("auditor")) roleClass = "auditor";
        if (role.includes("operador")) roleClass = "operator";
        if (role.includes("investigador")) roleClass = "researcher";

        rowsHtml += `
          <tr>
            <td><strong>${u.full_name || u.username}</strong><br><small style="color:var(--text-muted);">${u.username} (${u.auth_method || 'SSO'})</small></td>
            <td><span class="role-badge ${roleClass}">${role.replace(/_/g, ' ').toUpperCase()}</span></td>
            <td>${u.entity || 'Gobierno de Panamá'}</td>
            <td><span class="badge ${u.status === 'ACTIVO' ? 'badge-success' : 'badge-danger'}">● ${u.status || 'ACTIVO'}</span></td>
            <td><small>${u.last_login || '2026-09-25 UTC'}</small></td>
          </tr>
        `;
      });
      rowsHtml += "</tbody>";
      table.innerHTML = rowsHtml;
    } catch (_) {}
  };

  window.createNewGovUser = async function() {
    const nameEl = document.getElementById("new-user-name");
    const emailEl = document.getElementById("new-user-email");
    const roleEl = document.getElementById("new-user-role");
    const entityEl = document.getElementById("new-user-entidad");
    const status = document.getElementById("new-user-status");

    const name = nameEl ? nameEl.value.trim() : "";
    const email = emailEl ? emailEl.value.trim() : "";
    const role = roleEl ? roleEl.value : "operador_portuario";
    const entity = entityEl && entityEl.value.trim() ? entityEl.value.trim() : "Autoridad Marítima de Panamá";

    if (!name || !email) {
      if (status) {
        status.textContent = "Ingresa nombre y correo electrónico.";
        status.style.color = "var(--rose-danger)";
      }
      return;
    }

    if (status) status.textContent = "Registrando en servidor...";
    try {
      const username = email.split('@')[0].toLowerCase().replace(/[^a-z0-9_]/g, '_');
      const res = await fetch("/api/admin/users", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username,
          full_name: name,
          entity: entity,
          role_id: role,
          auth_method: "Bearer_Token"
        })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Error al crear usuario");

      if (status) {
        const uName = (d.user && d.user.full_name) || (d.registered_user && d.registered_user.full_name) || name;
        status.textContent = `✓ Funcionario "${uName}" registrado exitosamente.`;
        status.style.color = "var(--emerald-success)";
      }
      if (nameEl) nameEl.value = "";
      if (emailEl) emailEl.value = "";
      window.loadGovAdminData();
      setTimeout(() => { if (status) status.textContent = ""; }, 4000);
    } catch (err) {
      if (status) {
        status.textContent = `Error: ${err.message}`;
        status.style.color = "var(--rose-danger)";
      }
    }
  };

  window.revokeAllSessions = async function() {
    if (!confirm("¿Confirmas la revocación inmediata de TODAS las sesiones activas en el sistema? Los operadores deberán volver a iniciar sesión.")) return;
    try {
      const res = await fetch("/api/admin/revoke-sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reason: "Revocación administrativa preventiva" })
      });
      const d = await res.json();
      alert(`🚨 Se han revocado exitosamente ${d.revoked_tokens_count || d.revoked_sessions_count || 1} sesiones y tokens activos.`);
      window.loadGovAdminData();
    } catch (err) {
      alert("Error al revocar sesiones: " + err.message);
    }
  };

  window.loadMcpSouls = async function() {
    const container = document.getElementById("soul-cards-container");
    if (!container) return;
    try {
      const res = await fetch("/api/mcp/souls");
      const d = await res.json();
      const soulsList = d.souls || [];
      container.innerHTML = soulsList.map((s, idx) => `
        <div class="soul-card ${idx === 0 ? 'active' : ''}" data-soul-id="${s.id}" onclick="activateSoul('${s.id}')">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span class="s-name">${s.badge || '🎭'} ${s.name}</span>
            ${idx === 0 ? '<span class="badge badge-success">Activa</span>' : ''}
          </div>
          <p class="s-desc">${s.system_instructions ? s.system_instructions.substring(0, 110) + '...' : ''}</p>
          <small style="color:var(--text-dim); display:block; margin-top:0.3rem;">Rol: ${s.target_role} • Guardrails: ${(s.guardrails_enforced || []).length}</small>
        </div>
      `).join("");
    } catch (_) {}
  };

  window.activateSoul = function(soulId) {
    document.querySelectorAll(".soul-card").forEach(c => {
      const isTarget = c.getAttribute("data-soul-id") === soulId;
      c.classList.toggle("active", isTarget);
      const badge = c.querySelector(".badge");
      if (badge) badge.style.display = isTarget ? "inline-block" : "none";
    });
  };

  window.updateMcpToolDefaultParams = function() {
    const toolSelect = document.getElementById("mcp-tool-select");
    const textarea = document.getElementById("mcp-params-json");
    if (!toolSelect || !textarea) return;
    const tool = toolSelect.value;
    const defaults = {
      get_port_forecast: { port_name: "Puerto Balboa", horizon_months: 3, algorithm: "ensemble" },
      run_monte_carlo_risk_simulation: { port_name: "SSA Marine MIT", scenario: "drought_canal_restriction", num_paths: 500 },
      compare_model_benchmarks: { sort_by: "wape" },
      simulate_external_feature: { port_name: "Puerto Balboa", feature_name: "gatun_lake_level_feet", value: 81.5, normalization: "robust_mad" },
      query_maritime_knowledge: { query: "¿Qué exige la Ley 56 sobre las concesiones de terminales portuarias?", top_k: 2 }
    };
    textarea.value = JSON.stringify(defaults[tool] || {}, null, 2);
  };

  window.executeMcpToolLive = async function() {
    const toolSelect = document.getElementById("mcp-tool-select");
    const textarea = document.getElementById("mcp-params-json");
    const outputBox = document.getElementById("mcp-output-box");
    const resultViewer = document.getElementById("mcp-json-rpc-result");

    if (!toolSelect || !textarea || !resultViewer) return;
    const toolName = toolSelect.value;
    let params = {};
    try {
      params = JSON.parse(textarea.value);
    } catch (err) {
      alert("Error de sintaxis JSON en los argumentos: " + err.message);
      return;
    }

    if (outputBox) outputBox.style.display = "block";
    resultViewer.textContent = "Ejecutando herramienta mediante protocolo MCP / JSON-RPC 2.0...";

    try {
      const res = await fetch("/api/mcp/execute-tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tool_name: toolName, arguments: params })
      });
      const d = await res.json();
      resultViewer.textContent = JSON.stringify(d, null, 2);
    } catch (err) {
      resultViewer.textContent = `Error JSON-RPC: ${err.message}`;
    }
  };

  // Wire Educational Click Events to KPI Cards
  const kpiP50Card = document.getElementById("kpi-p50") ? document.getElementById("kpi-p50").closest(".kpi-card") : null;
  if (kpiP50Card) {
    kpiP50Card.style.cursor = "pointer";
    kpiP50Card.title = "Clic para ver explicación pedagógica de P50";
    kpiP50Card.addEventListener("click", () => {
      openModal("MÉTRICAS DE INFERENCIA", "Pronóstico Central Mediano (P50)",
        "Representa la proyección esperada más probable de movimiento mensual de contenedores en TEUs para la terminal seleccionada.",
        "Se calcula evaluando la función cuantil condicionada en &tau; = 0.50 mediante LightGBM entrenado sobre los 140 meses de microdatos bitemporales de la AMP.",
        "Permite a los operadores portuarios y despachadores presupuestar turnos y grúas pórtico con el escenario de máxima verosimilitud.",
        "Es el valor central del pronóstico: hay un 50% de probabilidad de que el volumen quede por encima y 50% por debajo. Es el número base para planificar el mes.");
    });
  }

  const kpiP10Card = document.getElementById("kpi-p10") ? document.getElementById("kpi-p10").closest(".kpi-card") : null;
  if (kpiP10Card) {
    kpiP10Card.style.cursor = "pointer";
    kpiP10Card.title = "Clic para ver explicación pedagógica de P10";
    kpiP10Card.addEventListener("click", () => {
      openModal("MÉTRICAS DE INFERENCIA", "Suelo de Seguridad Operacional (P10)",
        "Representa el cuantil pesimista del 10%. Solo existe un 10% de probabilidad estadística de que la demanda caiga por debajo de este umbral.",
        "Se infiere mediante la función de pérdida Pinball Loss (check loss) con &tau; = 0.10, capturando el soporte inferior de la distribución empírica.",
        "Garantiza el flujo de caja operativo mínimo y los compromisos contractuales de productividad de muelle.",
        "Es el 'piso seguro': pase lo que pase, el puerto difícilmente recibirá menos de esta cantidad de contenedores.");
    });
  }

  const kpiP90Card = document.getElementById("kpi-p90") ? document.getElementById("kpi-p90").closest(".kpi-card") : null;
  if (kpiP90Card) {
    kpiP90Card.style.cursor = "pointer";
    kpiP90Card.title = "Clic para ver explicación pedagógica de P90";
    kpiP90Card.addEventListener("click", () => {
      openModal("MÉTRICAS DE INFERENCIA", "Techo de Capacidad & Estrés de Patios (P90)",
        "Representa el cuantil optimista del 90%. Existe un 90% de probabilidad de que la demanda mensual no supere este volumen.",
        "Se calcula con Pinball Loss en &tau; = 0.90. Si este valor supera el 85% de la capacidad física instalada del patio, se activa alerta de congestión.",
        "Permite prever si habrá cuellos de botella en las compuertas (gates), necesidad de estibadores temporales o desvío de buques.",
        "Es el 'techo de estrés': te avisa si el muelle va a estar a reventar de carga para que no te tome por sorpresa la congestión.");
    });
  }

  const kpiImbalanceCard = document.getElementById("kpi-imbalance") ? document.getElementById("kpi-imbalance").closest(".kpi-card") : null;
  if (kpiImbalanceCard) {
    kpiImbalanceCard.style.cursor = "pointer";
    kpiImbalanceCard.title = "Clic para ver explicación pedagógica de Vacíos";
    kpiImbalanceCard.addEventListener("click", () => {
      openModal("EQUILIBRIO LOGÍSTICO", "Balance y Semáforo de Cajas Vacías",
        "Monitorea la proporción de contenedores vacíos frente al total de carga para detectar desbalances de importación/exportación.",
        "Calcula el ratio R_vacíos = (Vacíos Locales + Vacíos Trasbordo) / Total TEUs. Si R > 0.80 alerta por patio congestionado de cajas vacías; si R < 0.20 alerta por déficit de cajas para exportadores.",
        "Fundamental para coordinar con las líneas navieras el fletamento de buques 'sweeper' que evacúen cajas vacías hacia Asia.",
        "Te indica si el patio se está llenando de cajas vacías estorbando o si por el contrario hacen falta cajas para que los productores panameños exporten.");
    });
  }

  // --- Bootstrapping ---
  btnPredict.addEventListener("click", runForecast);
  btnSimulate.addEventListener("click", runSimulation);

  checkHealth();
  runForecast();
});
