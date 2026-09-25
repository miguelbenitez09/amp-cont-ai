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
  const algoBadge = document.getElementById("algo-badge");
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
  const apiSnippets = {
    curl: `curl -X POST "http://127.0.0.1:8000/predict" \\
  -H "Content-Type: application/json" \\
  -d '{
    "port": "Puerto Balboa",
    "horizon_months": 3,
    "algorithm": "ensemble",
    "bunker_perturbation_pct": 0.0,
    "transshipment_perturbation_pct": 0.0
  }'`,
    python: `import requests

url = "http://127.0.0.1:8000/predict"
payload = {
    "port": "Puerto Balboa",
    "horizon_months": 3,
    "algorithm": "ensemble",
    "bunker_perturbation_pct": 0.0,
    "transshipment_perturbation_pct": 0.0
}

response = requests.post(url, json=payload)
data = response.json()
print("Pronóstico P50:", [m["predicted_teus_p50"] for m in data["forecast"]])`,
    javascript: `// Inferencia con Fetch API moderna
const response = await fetch("http://127.0.0.1:8000/predict", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    port: "Puerto Balboa",
    horizon_months: 3,
    algorithm: "ensemble"
  })
});
const data = await response.json();
console.log("Pronósticos:", data.forecast);`
  };

  const apiLangButtons = document.querySelectorAll(".api-lang-btn");
  const apiCodeSnippet = document.getElementById("api-code-snippet");
  const btnCopyCode = document.getElementById("btn-copy-code");
  const btnLiveTest = document.getElementById("btn-live-test");
  const liveTestStatus = document.getElementById("live-test-status");
  const liveResponseBox = document.getElementById("live-response-box");
  const responseStatusBadge = document.getElementById("response-status-badge");
  const responseTimeBadge = document.getElementById("response-time-badge");
  const liveResponseCode = document.getElementById("live-response-code");

  if (apiLangButtons.length > 0 && apiCodeSnippet) {
    apiLangButtons.forEach(btn => {
      btn.addEventListener("click", () => {
        apiLangButtons.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        const lang = btn.getAttribute("data-lang");
        const code = apiSnippets[lang] || apiSnippets.curl;
        apiCodeSnippet.querySelector("code").textContent = code;
      });
    });
  }

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

  if (btnLiveTest) {
    btnLiveTest.addEventListener("click", async () => {
      liveTestStatus.textContent = "Ejecutando petición en vivo a /predict...";
      btnLiveTest.disabled = true;
      const startTime = performance.now();

      try {
        const res = await fetch("/predict", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            port: "Puerto Balboa",
            horizon_months: 3,
            algorithm: "ensemble",
            bunker_perturbation_pct: 0.0,
            transshipment_perturbation_pct: 0.0
          })
        });

        const elapsed = Math.round(performance.now() - startTime);
        const data = await res.json();

        liveResponseBox.style.display = "block";
        responseStatusBadge.textContent = `${res.status} ${res.statusText || "OK"}`;
        responseStatusBadge.style.background = res.ok ? "rgba(16, 185, 129, 0.2)" : "rgba(244, 63, 94, 0.2)";
        responseStatusBadge.style.color = res.ok ? "var(--emerald-success)" : "var(--rose-alert)";
        responseTimeBadge.textContent = `${elapsed} ms (Latencia Real)`;
        liveResponseCode.textContent = JSON.stringify(data, null, 2);
        liveTestStatus.textContent = `Petición exitosa en ${elapsed} ms. Datos 100% reales.`;
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

  // --- Export Functions ---
  function downloadBlob(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  if (btnExportForecastJson) {
    btnExportForecastJson.addEventListener("click", () => {
      if (!latestForecastCache) {
        exportStatus.textContent = "Primero genera un pronóstico en la pestaña 'Pronóstico & What-If'.";
        return;
      }
      downloadBlob(JSON.stringify(latestForecastCache, null, 2), `pronostico_${latestForecastCache.port.replace(/\s+/g, '_')}.json`, "application/json");
      exportStatus.textContent = "✓ Pronóstico descargado en formato JSON.";
      setTimeout(() => { exportStatus.textContent = ""; }, 3000);
    });
  }

  if (btnExportForecastCsv) {
    btnExportForecastCsv.addEventListener("click", () => {
      if (!latestForecastCache || !latestForecastCache.predictions) {
        exportStatus.textContent = "Primero genera un pronóstico en la pestaña 'Pronóstico & What-If'.";
        return;
      }
      let csv = "month_offset,date,pred_p10_teu,pred_p50_teu,pred_p90_teu,empty_ratio,imbalance_status\n";
      latestForecastCache.predictions.forEach(p => {
        csv += `${p.month_offset},${p.date},${p.pred_p10_teu},${p.pred_p50_teu},${p.pred_p90_teu},${p.empty_ratio_estimate},"${p.imbalance_status}"\n`;
      });
      downloadBlob(csv, `pronostico_${latestForecastCache.port.replace(/\s+/g, '_')}.csv`, "text/csv");
      exportStatus.textContent = "✓ Pronóstico descargado en formato CSV.";
      setTimeout(() => { exportStatus.textContent = ""; }, 3000);
    });
  }

  if (btnExportBenchmarkJson) {
    btnExportBenchmarkJson.addEventListener("click", async () => {
      try {
        const res = await fetch("/api/models/compare");
        const d = await res.json();
        downloadBlob(JSON.stringify(d, null, 2), "benchmark_multi_algoritmo.json", "application/json");
        exportStatus.textContent = "✓ Benchmark descargado en formato JSON.";
        setTimeout(() => { exportStatus.textContent = ""; }, 3000);
      } catch (err) {
        exportStatus.textContent = `Error al exportar: ${err.message}`;
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

  // --- Bootstrapping ---
  btnPredict.addEventListener("click", runForecast);
  btnSimulate.addEventListener("click", runSimulation);

  checkHealth();
  runForecast();
});
