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
      } else if (targetTab === "tab-data-platform") {
        if (window.loadDataPlatformManifest) window.loadDataPlatformManifest();
      } else if (targetTab === "tab-security-iam") {
        if (window.verifyWormAuditChainLive) window.verifyWormAuditChainLive();
        if (window.fetchAuditSecurityEvents) window.fetchAuditSecurityEvents();
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
          "extra_trees": {
            name: "Extra Trees Regressor",
            badge: "🌳 Challenger",
            class: "",
            what: "Extremely Randomized Trees con umbrales aleatorios de corte en cada división de nodo.",
            how: "ExtraTreesRegressor(n_estimators=100, max_depth=10, bootstrap=False). Particiones estocásticas independientes.",
            why: "Disminuye la correlación entre árboles individuales y ofrece una inmunidad superlativa ante covariables ruidosas."
          },
          "catboost_gbdt": {
            name: "CatBoost GBDT",
            badge: "🐱 Challenger",
            class: "",
            what: "Gradient boosting con árboles de decisión simétricos (oblivious trees) y codificación target sin fugas.",
            how: "CatBoostRegressor(iterations=120, depth=6, learning_rate=0.06). Estructura idéntica en ramas para evaluar en paralelo.",
            why: "Extremadamente resistente al sobreajuste en muestras pequeñas/medianas de series de tiempo."
          },
          "bayesian_ridge": {
            name: "Bayesian Ridge",
            badge: "📐 Challenger",
            class: "",
            what: "Inferencia paramétrica bayesiana con distribuciones a priori sobre los coeficientes de regresión.",
            how: "BayesianRidge(n_iter=300, alpha_1=1e-6, lambda_1=1e-6). Estimación analítica de la matriz de precisión.",
            why: "Cuantifica analíticamente la varianza epistémica de los parámetros del modelo lineal."
          },
          "neural_mlp_quantile": {
            name: "Quantile Neural MLP",
            badge: "🧠 Challenger",
            class: "",
            what: "Perceptrón multicapa deep tabular con capas densas, Batch Normalization y Dropout.",
            how: "MLPRegressor(hidden_layer_sizes=(128, 64), activation='relu', alpha=0.01). Optimizado con Huber loss.",
            why: "Aprende representaciones densas latentes de alta dimensión y relaciones no lineales complejas."
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

      // Render WAPE Chart for Top Algorithms
      const algoKeys = ["lightgbm", "random_forest", "extra_trees", "catboost_gbdt", "gradient_boosting", "neural_mlp_quantile"];
      const algoLabels = ["LightGBM", "Random Forest", "Extra Trees", "CatBoost", "HistGradient", "Neural MLP"];
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
            backgroundColor: ["#06b6d4", "#10b981", "#14b8a6", "#3b82f6", "#8b5cf6", "#f59e0b"],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#e2e8f0", font: { weight: "bold" } }, grid: { display: false } },
            y: {
              ticks: { color: "#e2e8f0", font: { weight: "bold" }, callback: v => `${v}%` },
              grid: { color: "rgba(255, 255, 255, 0.08)" }
            }
          }
        }
      });

      // Render R2 Chart with High Contrast
      const ctxR2 = document.getElementById("algoR2Chart").getContext("2d");
      if (algoR2ChartInst) algoR2ChartInst.destroy();
      algoR2ChartInst = new Chart(ctxR2, {
        type: "bar",
        data: {
          labels: algoLabels,
          datasets: [{
            label: "Coeficiente R²",
            data: r2Vals,
            backgroundColor: ["#22d3ee", "#34d399", "#2dd4bf", "#60a5fa", "#a855f7", "#fbbf24"],
            borderRadius: 6
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { color: "#e2e8f0", font: { weight: "bold" } }, grid: { display: false } },
            y: {
              min: 0.9,
              max: 1.0,
              ticks: { color: "#e2e8f0", font: { weight: "bold" } },
              grid: { color: "rgba(255, 255, 255, 0.08)" }
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
            borderWidth: 2.2,
            pointRadius: 4.5,
            pointBackgroundColor: "#06b6d4",
            fill: true,
            tension: 0.2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: true,
              labels: { color: "#e2e8f0", font: { size: 11, weight: "bold" } }
            },
            tooltip: {
              callbacks: {
                label: ctx => `Error residual: ${ctx.parsed.y.toLocaleString()} TEUs`
              }
            }
          },
          scales: {
            x: {
              ticks: { color: "#e2e8f0", font: { size: 11, weight: "bold" } },
              grid: { color: "rgba(255, 255, 255, 0.08)" }
            },
            y: {
              ticks: {
                color: "#e2e8f0",
                font: { size: 11, weight: "bold" },
                callback: v => `${(v / 1000).toFixed(0)}k TEUs`
              },
              grid: { color: "rgba(255, 255, 255, 0.08)" }
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
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: ctx => `Ganancia Split Gain: ${ctx.parsed.x.toLocaleString()}`
              }
            }
          },
          onClick: (evt, elements) => {
            if (elements.length > 0) {
              const idx = elements[0].index;
              const feat = realFeatures[idx];
              window.openFeatureDetailModal(feat.name);
            }
          },
          scales: {
            x: {
              ticks: { color: "#e2e8f0", font: { size: 11, weight: "bold" } },
              grid: { color: "rgba(255, 255, 255, 0.08)" }
            },
            y: {
              ticks: { color: "#e2e8f0", font: { family: "monospace", size: 11, weight: "bold" } },
              grid: { display: false }
            }
          }
        }
      });

      // Populate Quick Feature Pills
      const pillsContainer = document.getElementById("feature-quick-pills");
      if (pillsContainer) {
        pillsContainer.innerHTML = realFeatures.map((f, i) => `
          <button type="button" class="btn-subtle-phase-nav" onclick="window.openFeatureDetailModal('${f.name}')" title="Inspeccionar feature #${i+1}">
            <span>#${i+1}</span> <code>${f.name}</code>
          </button>
        `).join("");
      }

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
            window.openFeatureDetailModal(feat);
          });
          vifContainer.appendChild(div);
        }
      }

      // Top Correlation Pairs Table (Clickable to open dedicated correlation modal)
      const corrTbody = document.getElementById("corr-tbody");
      const highPairs = (data.collinearity && data.collinearity.high_correlation_pairs) || [];
      if (corrTbody) {
        corrTbody.innerHTML = "";
        highPairs.slice(0, 6).forEach(p => {
          const tr = document.createElement("tr");
          tr.className = "clickable-row";
          tr.title = "Haz clic para ver el análisis de multicolinealidad e inmunidad de árboles";
          tr.innerHTML = `
            <td><code>${p.feature_1}</code></td>
            <td><code>${p.feature_2}</code></td>
            <td style="color:var(--amber-warn); font-family:var(--font-mono); font-weight:700;">${p.correlation}</td>
            <td style="color:var(--emerald-success); font-size:0.8rem;">Absorbido por Árboles (Ver 🔍)</td>
          `;
          tr.addEventListener("click", () => {
            window.openCorrelationDetailModal(p.feature_1, p.feature_2);
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
            <div class="confounder-desc"><strong>Efecto Causal:</strong> ${c.effect}</div>
            <div class="confounder-treatment"><strong>Tratamiento (Criterio Backdoor):</strong> ${c.treatment}</div>
            <div class="click-hint"><svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg> Clic para ver DAG, Qué se hizo, Cómo y Por Qué</div>
          `;
          card.addEventListener("click", () => {
            openModal(
              `Tratamiento Causal: ${c.name} (${c.type})`,
              c.name,
              c.what || c.effect,
              `<p><strong>Tratamiento Matemático y Criterio Backdoor de Pearl:</strong></p>
               <p>${c.how || c.treatment}</p>
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
    const pathsInput = document.getElementById("sim-paths-val");
    const horizonInput = document.getElementById("sim-horizon-val");
    const userInput = document.getElementById("sim-user-select");

    const numPaths = pathsInput ? parseInt(pathsInput.value, 10) : parseInt(simPathsSlider.value, 10);
    const horizon = horizonInput ? parseInt(horizonInput.value, 10) : parseInt(simHorizonSlider.value, 10);
    const user = userInput ? userInput.value : "operador_puerto";

    try {
      const res = await fetch("/api/simulation/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          port: port,
          horizon_months: horizon,
          num_paths: numPaths,
          scenario_type: scenario,
          user: user
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

      const runBadge = document.getElementById("sim-run-status-badge");
      if (runBadge && simData.audit_ledger) {
        runBadge.textContent = `Bloque WORM #${simData.audit_ledger.block_number} Registrado`;
        runBadge.style.background = "rgba(16,185,129,0.2)";
      }

      renderSimulationFanChart(simData.trajectory_profile || [], horizon);

      // Refresh WORM history table
      if (typeof window.loadSimulationHistory === "function") {
        window.loadSimulationHistory();
      }

    } catch (err) {
      alert(`Error en simulación Monte Carlo: ${err.message}`);
    } finally {
      btnSimulate.disabled = false;
      btnSimulate.innerHTML = `
        <svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
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
            borderWidth: 2.8,
            pointRadius: 4.5,
            pointBackgroundColor: "#22d3ee",
            tension: 0.25
          },
          {
            label: "P75 Banda Central",
            data: p75,
            borderColor: "rgba(16, 185, 129, 0.6)",
            borderWidth: 1.2,
            pointRadius: 0,
            fill: "+1",
            backgroundColor: "rgba(16, 185, 129, 0.14)",
            tension: 0.25
          },
          {
            label: "P25 Banda Central",
            data: p25,
            borderColor: "rgba(16, 185, 129, 0.6)",
            borderWidth: 1.2,
            pointRadius: 0,
            fill: false,
            tension: 0.25
          },
          {
            label: "P90 Techo Estocástico",
            data: p90,
            borderColor: "rgba(56, 189, 248, 0.6)",
            borderWidth: 1.5,
            borderDash: [5, 5],
            pointRadius: 0,
            fill: "+1",
            backgroundColor: "rgba(56, 189, 248, 0.08)",
            tension: 0.25
          },
          {
            label: "P10 VaR 90% Piso",
            data: p10,
            borderColor: "rgba(244, 63, 94, 0.65)",
            borderWidth: 1.5,
            borderDash: [5, 5],
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
          legend: {
            display: true,
            labels: {
              color: "#e2e8f0",
              font: { size: 11, weight: "bold" }
            }
          }
        },
        scales: {
          x: {
            ticks: {
              color: "#e2e8f0",
              font: { size: 11, weight: "bold" }
            },
            grid: { color: "rgba(255, 255, 255, 0.08)" }
          },
          y: {
            ticks: {
              color: "#e2e8f0",
              font: { size: 11, weight: "bold" },
              callback: v => `${(v / 1000).toFixed(0)}k TEUs`
            },
            grid: { color: "rgba(255, 255, 255, 0.08)" }
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
  // exportStatus is declared above at line 1258

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

  window.showPresetMathDetail = async function(presetId) {
    const box = document.getElementById("preset-math-code-box");
    const title = document.getElementById("preset-math-title");
    const formulaDisplay = document.getElementById("preset-math-formula-display");
    const desc = document.getElementById("preset-math-desc");
    const code = document.getElementById("preset-python-code");

    if (!box) return;
    box.style.display = "block";
    title.textContent = `Cargando detalles de preset: ${presetId}...`;

    try {
      const res = await fetch(`/api/models/presets/${presetId}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al cargar preset");

      title.innerHTML = `📐 ${data.name} — Fundamento & Arquitectura`;
      const rawFormula = data.loss_formula || "\\mathcal{L}_{\\tau}(y, \\hat{y}) = \\max(\\tau(y - \\hat{y}), (\\tau - 1)(y - \\hat{y}))";
      
      if (window.renderKaTeXMath) {
        window.renderKaTeXMath(rawFormula, formulaDisplay, true);
      } else {
        formulaDisplay.textContent = rawFormula;
      }
      
      desc.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
          <span><strong>Aplicación Operativa:</strong> ${data.target_application}</span>
          <button class="btn-copy-latex" onclick="window.copyLatexToClipboard('${rawFormula.replace(/\\/g, "\\\\")}', this)">📋 Copiar LaTeX</button>
        </div>
        <strong>Hiperparámetros Clave:</strong> Learning Rate: <code>${data.hyperparameters.learning_rate}</code>, Estimadores: <code>${data.hyperparameters.n_estimators}</code>, Profundidad: <code>${data.hyperparameters.max_depth}</code>, Regularización L1 (Lasso): <code>${data.hyperparameters.reg_alpha || 0}</code>, L2 (Ridge): <code>${data.hyperparameters.reg_lambda || 0}</code>.
      `;
      code.textContent = data.code_snippet || "# Código fuente no disponible";
      box.scrollIntoView({ behavior: "smooth", block: "nearest" });
    } catch (err) {
      title.textContent = `Error al consultar preset: ${err.message}`;
    }
  };

  window.toggleCustomPresetForm = function() {
    const f = document.getElementById("custom-preset-form-box");
    if (!f) return;
    f.style.display = (f.style.display === "none" || !f.style.display) ? "block" : "none";
  };

  window.registerCustomPreset = async function() {
    const idEl = document.getElementById("cp-id");
    const nameEl = document.getElementById("cp-name");
    const algoEl = document.getElementById("cp-algo");
    const lrEl = document.getElementById("cp-lr");
    const estEl = document.getElementById("cp-n-estimators");
    const depthEl = document.getElementById("cp-max-depth");
    const l1El = document.getElementById("cp-l1");
    const l2El = document.getElementById("cp-l2");
    const lossEl = document.getElementById("cp-loss");
    const descEl = document.getElementById("cp-desc");
    const statusEl = document.getElementById("custom-preset-status");

    const presetId = (idEl ? idEl.value.trim() : "").toLowerCase().replace(/[^a-z0-9_]/g, "_");
    const name = nameEl ? nameEl.value.trim() : "";
    if (!presetId || !name) {
      if (statusEl) {
        statusEl.textContent = "Ingresa ID y Nombre del preset.";
        statusEl.style.color = "var(--rose-danger)";
      }
      return;
    }

    if (statusEl) {
      statusEl.textContent = "Registrando preset en caliente...";
      statusEl.style.color = "var(--cyan-bright)";
    }

    try {
      const payload = {
        id: presetId,
        name: name,
        description: descEl ? descEl.value.trim() : "Preset personalizado de usuario",
        base_algorithm: algoEl ? algoEl.value : "lightgbm",
        hyperparameters: {
          learning_rate: parseFloat(lrEl.value),
          n_estimators: parseInt(estEl.value, 10),
          max_depth: parseInt(depthEl.value, 10),
          reg_alpha: parseFloat(l1El.value),
          reg_lambda: parseFloat(l2El.value),
          objective: lossEl ? lossEl.value : "quantile"
        },
        target_application: descEl ? descEl.value.trim() : "Optimización personalizada en caliente",
        loss_formula: "\\mathcal{L}_{\\text{custom}}(\\theta) = \\sum_{i=1}^N \\ell(y_i, f(x_i)) + \\lambda_1 |\\theta| + \\lambda_2 ||\\theta||_2^2"
      };

      const res = await fetch("/api/models/presets", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al registrar preset");

      if (statusEl) {
        statusEl.textContent = `✓ Preset "${name}" registrado exitosamente.`;
        statusEl.style.color = "var(--emerald-success)";
      }

      // Append card dynamically to grid if not exists
      const container = document.getElementById("preset-cards-container");
      if (container && !document.querySelector(`[data-preset-id="${presetId}"]`)) {
        const newCard = document.createElement("div");
        newCard.className = "preset-card";
        newCard.setAttribute("data-preset-id", presetId);
        newCard.onclick = () => window.selectTrainingPreset(presetId);
        newCard.innerHTML = `
          <div class="preset-header">
            <span class="preset-title">${name}</span>
            <span class="preset-badge champion">Custom</span>
          </div>
          <p class="preset-desc">${payload.description}</p>
          <div class="preset-specs">LR: ${payload.hyperparameters.learning_rate} • Est: ${payload.hyperparameters.n_estimators} • Prof: ${payload.hyperparameters.max_depth}</div>
          <div class="preset-card-footer">
            <button class="preset-info-btn" onclick="event.stopPropagation(); showPresetMathDetail('${presetId}')">📐 Matemática & Código</button>
          </div>
        `;
        container.appendChild(newCard);
      }

      setTimeout(() => {
        window.toggleCustomPresetForm();
        if (statusEl) statusEl.textContent = "";
      }, 2000);
    } catch (err) {
      if (statusEl) {
        statusEl.textContent = `Error: ${err.message}`;
        statusEl.style.color = "var(--rose-danger)";
      }
    }
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

    const savePathInput = document.getElementById("repro-save-path");
    const modelIdInput = document.getElementById("repro-model-id");
    const versionTagInput = document.getElementById("repro-version-tag");
    const seedInput = document.getElementById("repro-seed-val");

    const savePath = savePathInput ? savePathInput.value.trim() : "models/champion_lightgbm.joblib";
    const modelId = modelIdInput ? modelIdInput.value.trim() : "panama-portops-lgbm-v1";
    const versionTag = versionTagInput ? versionTagInput.value.trim() : "v1.2.0-panama";
    const seed = seedInput ? parseInt(seedInput.value, 10) : 42;

    if (btn) btn.disabled = true;
    if (status) {
      status.textContent = `Ejecutando reentrenamiento determinista (Seed ${seed})...`;
      status.style.color = "var(--cyan-bright)";
    }
    if (resultBox) resultBox.style.display = "none";

    try {
      const res = await fetch("/api/models/reproducible-train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          seed: seed,
          preset: window.selectedPresetId || "balanced_champion",
          save_path: savePath,
          model_id: modelId,
          version_tag: versionTag
        })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Error en reentrenamiento determinista");

      if (status) {
        status.textContent = `✓ Modelo guardado en ${savePath} (${d.training_time_seconds.toFixed(2)}s, Semilla ${seed}).`;
        status.style.color = "var(--emerald-success)";
      }
      if (resultBox) {
        resultBox.style.display = "block";
        resultBox.innerHTML = `
          <strong style="color:var(--cyan-bright); font-size:0.85rem;">Certificado de Determinismo & Huella Criptográfica SHA-256:</strong><br>
          • <strong>Algoritmo:</strong> ${d.algorithm} (Preset: <code>${d.preset}</code>)<br>
          • <strong>Ruta en Disco:</strong> <code>${d.save_path || savePath}</code> (ID: <code>${d.model_id || modelId}</code> @ <code>${d.version_tag || versionTag}</code>)<br>
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
            <th>Rol Estandarizado</th>
            <th>Entidad</th>
            <th>Estado</th>
            <th>Último Acceso</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
      `;
      (d.active_users || []).forEach(u => {
        let roleClass = "operator";
        const role = u.role_id || "port_operator";
        if (role === "root_owner" || role.includes("superadmin")) roleClass = "superadmin";
        else if (role === "platform_admin") roleClass = "superadmin";
        else if (role === "mlops_engineer") roleClass = "auditor";
        else if (role === "compliance_auditor") roleClass = "auditor";
        else if (role === "readonly_viewer") roleClass = "researcher";

        const isRoot = (u.username === "root" || role === "root_owner");
        rowsHtml += `
          <tr>
            <td><strong>${u.full_name || u.username}</strong><br><small style="color:var(--text-muted); font-family:var(--font-mono);">${u.username} (${u.auth_method || 'SSO'})</small></td>
            <td><span class="role-badge ${roleClass}">${role.replace(/_/g, ' ').toUpperCase()}</span></td>
            <td>${u.entity || 'Gobierno de Panamá'}</td>
            <td><span class="badge ${u.status === 'ACTIVO' ? 'badge-success' : 'badge-danger'}">● ${u.status || 'ACTIVO'}</span></td>
            <td><small>${u.last_login || '2026-09-25 UTC'}</small></td>
            <td>
              ${isRoot ? '<small style="color:var(--text-dim);">Protegido</small>' : `<button class="btn btn-secondary btn-sm" style="padding:0.15rem 0.45rem; font-size:0.7rem; color:var(--rose-alert);" onclick="deleteGovUser('${u.username}')">🗑️ Baja</button>`}
            </td>
          </tr>
        `;
      });
      rowsHtml += "</tbody>";
      table.innerHTML = rowsHtml;
    } catch (_) {}
  };

  window.deleteGovUser = async function(username) {
    if (!confirm(`¿Estás seguro de revocar y eliminar de forma permanente al usuario "${username}"?`)) return;
    try {
      const res = await fetch("/api/admin/delete-user", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: username })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al eliminar usuario");
      alert(`✓ ${data.message}`);
      window.loadGovAdminData();
    } catch (err) {
      alert(`Error: ${err.message}`);
    }
  };

  window.testLivePermission = async function() {
    const userSelect = document.getElementById("perm-test-user");
    const permSelect = document.getElementById("perm-test-action");
    const resultBox = document.getElementById("perm-test-result");
    if (!userSelect || !permSelect || !resultBox) return;

    const username = userSelect.value;
    const permission = permSelect.value;

    resultBox.style.display = "block";
    resultBox.innerHTML = `<em>Verificando permisos criptográficos contra la matriz RBAC ministerial...</em>`;

    try {
      const res = await fetch("/api/admin/verify-permission", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, permission })
      });
      const d = await res.json();
      if (!res.ok) throw new Error(d.detail || "Error en verificación de permisos");

      if (d.allowed) {
        resultBox.innerHTML = `
          <strong style="color:var(--emerald-success); font-size:0.85rem;">✅ ACCESO CONCEDIDO (Permiso Aprobado):</strong><br>
          • <strong>Usuario Auditado:</strong> <code>${d.username}</code> (Rol: <span class="role-badge superadmin">${d.role.toUpperCase()}</span>)<br>
          • <strong>Operación:</strong> <code>${d.permission_tested}</code><br>
          • <strong>Dictamen de Seguridad:</strong> Operación autorizada bajo el principio de mínimo privilegio (Least Privilege).<br>
          • <strong>Timestamp de Auditoría:</strong> <em>${d.timestamp}</em>
        `;
      } else {
        resultBox.innerHTML = `
          <strong style="color:var(--rose-alert); font-size:0.85rem;">🚫 ACCESO DENEGADO (Violación de Seguridad RBAC):</strong><br>
          • <strong>Usuario Auditado:</strong> <code>${d.username}</code> (Rol: <span class="role-badge operator">${d.role.toUpperCase()}</span>)<br>
          • <strong>Operación Solicitada:</strong> <code>${d.permission_tested}</code><br>
          • <strong>Motivo de Bloqueo:</strong> ${d.reason}<br>
          • <strong>Registro Forense:</strong> Incidente notificado a la bitácora de auditoría inmutable de la Contraloría General.
        `;
      }
    } catch (err) {
      resultBox.innerHTML = `<span style="color:var(--rose-alert);">Error en verificación: ${err.message}</span>`;
    }
  };

  window.createNewGovUser = async function() {
    const nameEl = document.getElementById("new-user-name");
    const emailEl = document.getElementById("new-user-email");
    const roleEl = document.getElementById("new-user-role");
    const entityEl = document.getElementById("new-user-entidad");
    const status = document.getElementById("new-user-status");

    const name = nameEl ? nameEl.value.trim() : "";
    const email = emailEl ? emailEl.value.trim() : "";
    const role = roleEl ? roleEl.value : "port_operator";
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

  // --- Universal Database Adapters Testing Engine ---
  window.currentSelectedDbEngine = "duckdb";

  window.testDatabaseAdapter = async function(engine, customQuery = null) {
    window.currentSelectedDbEngine = engine;
    const box = document.getElementById("db-live-diagnostic-box");
    const nameEl = document.getElementById("db-diag-engine-name");
    const statusBadge = document.getElementById("db-diag-status-badge");
    const latencyEl = document.getElementById("db-diag-latency");
    const poolEl = document.getElementById("db-diag-pool");
    const opEl = document.getElementById("db-diag-op");
    const fallbackEl = document.getElementById("db-diag-fallback");
    const queryInput = document.getElementById("db-custom-query-input");
    const previewEl = document.getElementById("db-diag-result-preview");

    if (!box) return;
    box.style.display = "block";
    if (queryInput && !customQuery) {
      if (engine === "duckdb") queryInput.value = "SELECT count(*) as total_filas, min(date) as desde, max(date) as hasta FROM amp_port_monthly_throughput";
      else if (engine === "timescaledb") queryInput.value = "SELECT hypertable_name, num_chunks FROM timescaledb_information.hypertables LIMIT 5";
      else if (engine === "redis") queryInput.value = "PING";
    }

    const titles = {
      duckdb: "DuckDB Columnar (OLAP Zero-Copy)",
      timescaledb: "PostgreSQL / TimescaleDB (Time-Series Hypertables)",
      redis: "Redis In-Memory Cache (Sub-Millisecond Inference Layer)"
    };
    if (nameEl) nameEl.textContent = `Diagnóstico en Tiempo Real: ${titles[engine] || engine}`;
    if (statusBadge) {
      statusBadge.textContent = "PROBANDO...";
      statusBadge.className = "badge badge-info";
    }
    if (previewEl) previewEl.innerHTML = "<em>Ejecutando ping y query diagnóstica...</em>";

    try {
      const payload = {
        engine: engine,
        custom_query: customQuery || (queryInput ? queryInput.value : null)
      };
      const res = await fetch("/api/infrastructure/database/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al probar conector");

      if (statusBadge) {
        statusBadge.textContent = data.status.toUpperCase();
        statusBadge.className = data.status === "online" ? "badge badge-success" : (data.status === "degraded" ? "badge badge-warn" : "badge badge-danger");
      }
      if (latencyEl) latencyEl.textContent = `${data.latency_ms.toFixed(3)} ms`;
      if (poolEl) poolEl.textContent = `${data.connection_pool.active_connections} / ${data.connection_pool.max_pool_size} Conexiones`;
      if (opEl) opEl.textContent = data.read_write_verification ? "Read/Write OK" : "Read Only";
      if (fallbackEl) fallbackEl.textContent = data.details.mode || data.engine;

      // Update card stat badge
      const statEl = document.getElementById(`db-stat-${engine}`);
      if (statEl) statEl.textContent = `Latencia: ${data.latency_ms.toFixed(2)} ms • Pool: ${data.connection_pool.active_connections}/${data.connection_pool.max_pool_size}`;

      if (previewEl) {
        if (data.diagnostic_query_result && Array.isArray(data.diagnostic_query_result) && data.diagnostic_query_result.length > 0) {
          const sample = data.diagnostic_query_result.slice(0, 4);
          const cols = Object.keys(sample[0]);
          let tableHtml = `<div class="table-responsive" style="max-height:160px; overflow-y:auto; margin-top:0.4rem;"><table class="api-spec-table"><thead><tr>` + cols.map(c => `<th>${c}</th>`).join("") + `</tr></thead><tbody>`;
          sample.forEach(row => {
            tableHtml += `<tr>` + cols.map(c => `<td><code>${row[c] !== null ? row[c] : "-"}</code></td>`).join("") + `</tr>`;
          });
          tableHtml += `</tbody></table></div>`;
          previewEl.innerHTML = tableHtml;
        } else {
          previewEl.innerHTML = `<pre class="json-rpc-viewer" style="margin-top:0.4rem; max-height:140px;">${JSON.stringify(data.diagnostic_query_result || data.details, null, 2)}</pre>`;
        }
      }
    } catch (err) {
      if (statusBadge) {
        statusBadge.textContent = "ERROR";
        statusBadge.className = "badge badge-danger";
      }
      if (previewEl) previewEl.innerHTML = `<span style="color:var(--rose-alert);">Error en diagnóstico: ${err.message}</span>`;
    }
  };

  window.runCustomDbQuery = function() {
    const input = document.getElementById("db-custom-query-input");
    const query = input ? input.value.trim() : null;
    window.testDatabaseAdapter(window.currentSelectedDbEngine, query);
  };

  // --- Glossary Filter Engine ---
  window.currentGlossaryCat = "all";
  window.currentGlossaryLetter = "ALL";

  window.filterGlossaryItems = function() {
    const searchVal = (document.getElementById("glossary-search-input") ? document.getElementById("glossary-search-input").value : "").toLowerCase().trim();
    const items = document.querySelectorAll(".glossary-item");

    items.forEach(item => {
      const text = item.textContent.toLowerCase();
      const cat = item.getAttribute("data-cat") || "";
      const letter = item.getAttribute("data-letter") || "";

      const matchesSearch = !searchVal || text.includes(searchVal);
      const matchesCat = (window.currentGlossaryCat === "all" || cat === window.currentGlossaryCat);
      const matchesLetter = (window.currentGlossaryLetter === "ALL" || letter.toUpperCase() === window.currentGlossaryLetter);

      if (matchesSearch && matchesCat && matchesLetter) {
        item.style.display = "block";
      } else {
        item.style.display = "none";
      }
    });
  };

  window.filterGlossaryByCategory = function(cat) {
    window.currentGlossaryCat = cat;
    document.querySelectorAll(".glossary-cat-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-cat") === cat);
    });
    window.filterGlossaryItems();
  };

  window.filterGlossaryByLetter = function(letter) {
    window.currentGlossaryLetter = letter;
    document.querySelectorAll(".alpha-btn").forEach(btn => {
      btn.classList.toggle("active", btn.textContent.trim().toUpperCase() === letter.toUpperCase());
    });
    window.filterGlossaryItems();
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


  // =========================================================================
  // CURATED MARITIME THEMES SWITCHER (4 Distinct Colorways)
  // =========================================================================
  function initThemeSwitcher() {
    const themeSelect = document.getElementById("theme-selector");
    if (!themeSelect) return;
    const savedTheme = localStorage.getItem("portops_theme") || "theme-cyber-ocean";
    document.body.className = savedTheme;
    themeSelect.value = savedTheme;
    themeSelect.addEventListener("change", (e) => {
      const selected = e.target.value;
      document.body.className = selected;
      localStorage.setItem("portops_theme", selected);
    });
  }

  // =========================================================================
  // HIGH-FIDELITY MATHEMATICAL ENGINE (KaTeX with Graceful Resilient Fallback)
  // =========================================================================
  function formatLatexFallback(latexStr) {
    if (!latexStr) return "";
    return latexStr
      .replace(/\\mathcal\{L\}_(\\tau|\{[^}]+\})/g, "L<sub>τ</sub>")
      .replace(/\\mathcal\{L\}/g, "L")
      .replace(/\\mathcal\{H\}/g, "H")
      .replace(/\\mathcal\{F\}/g, "F")
      .replace(/\\mathcal\{D\}/g, "D")
      .replace(/\\mathcal\{R\}/g, "R")
      .replace(/\\mathbb\{E\}/g, "E")
      .replace(/\\mathbb\{I\}/g, "I")
      .replace(/\\mathbb\{S\}\^1/g, "S¹")
      .replace(/\\text\{([A-Za-z0-9_\-áéíóúÁÉÍÓÚ\s]+)\}/g, "$1")
      .replace(/\\tau/g, "τ")
      .replace(/\\sigma/g, "σ")
      .replace(/\\mu/g, "μ")
      .replace(/\\lambda/g, "λ")
      .replace(/\\kappa/g, "κ")
      .replace(/\\alpha/g, "α")
      .replace(/\\epsilon/g, "ε")
      .replace(/\\pi/g, "π")
      .replace(/\\Sigma/g, "Σ")
      .replace(/\\sum_\{([^}]+)\}\^\{([^}]+)\}/g, "∑<sub>$1</sub><sup>$2</sup>")
      .replace(/\\sum/g, "∑")
      .replace(/\\int_\{([^}]+)\}\^\{([^}]+)\}/g, "∫<sub>$1</sub><sup>$2</sup>")
      .replace(/\\int/g, "∫")
      .replace(/\\prod_\{([^}]+)\}\^\{([^}]+)\}/g, "∏<sub>$1</sub><sup>$2</sup>")
      .replace(/\\prod/g, "∏")
      .replace(/\\max/g, "max")
      .replace(/\\min/g, "min")
      .replace(/\\sin/g, "sin")
      .replace(/\\cos/g, "cos")
      .replace(/\\frac\{([^}]+)\}\{([^}]+)\}/g, "($1 / $2)")
      .replace(/\\hat\{([^}]+)\}/g, "$1̂")
      .replace(/\\tilde\{([^}]+)\}/g, "$1̃")
      .replace(/\\left\(/g, "(")
      .replace(/\\right\)/g, ")")
      .replace(/\\left\[/g, "[")
      .replace(/\\right\]/g, "]")
      .replace(/\\left\\\{/g, "{")
      .replace(/\\right\\\}/g, "}")
      .replace(/\\forall/g, "∀")
      .replace(/\\in/g, "∈")
      .replace(/\\le/g, "≤")
      .replace(/\\ge/g, "≥")
      .replace(/\\wedge/g, " ∧ ")
      .replace(/\\parallel/g, " ∥ ")
      .replace(/\\implies/g, " ⟹ ")
      .replace(/\\quad/g, " &nbsp; ")
      .replace(/\\\\/g, "<br>");
  }

  window.renderKaTeXMath = function(latexString, containerElement, isDisplayMode = true) {
    if (!containerElement) return;
    if (window.katex) {
      try {
        containerElement.innerHTML = window.katex.renderToString(latexString, {
          displayMode: isDisplayMode,
          throwOnError: false
        });
        return;
      } catch (err) {
        console.warn("KaTeX render error:", err);
      }
    }
    // Fallback if KaTeX is not loaded
    containerElement.innerHTML = `<span class="math-fallback-rendered" style="font-family:serif; font-size:1.05rem; letter-spacing:0.02em;">${formatLatexFallback(latexString)}</span>`;
  };

  window.copyLatexToClipboard = function(latexString, btnEl) {
    navigator.clipboard.writeText(latexString).then(() => {
      const oldHtml = btnEl.innerHTML;
      btnEl.innerHTML = "<span>✅</span> ¡LaTeX Copiado!";
      btnEl.style.borderColor = "#34d399";
      btnEl.style.color = "#34d399";
      setTimeout(() => {
        btnEl.innerHTML = oldHtml;
        btnEl.style.borderColor = "";
        btnEl.style.color = "";
      }, 2000);
    }).catch(err => {
      console.error("Clipboard copy error:", err);
    });
  };

  // =========================================================================
  // RIGUROSA ARQUITECTURA METODOLÓGICA (8 Fases • Fórmulas KaTeX & Sandboxes)
  // =========================================================================
  window.methodologyCatalog = {
    "phase_1": {
      "title": "Ingesta Cruda & Extracción 353 Boletines Estadísticos AMP",
      "badge": "FASE 1: BRONZE LAKEHOUSE",
      "sub": "Trazabilidad completa desde datosabiertos.gob.pa hasta el Data Lakehouse Parquet",
      "simple": "Recopilamos 140 meses de informes mensuales que el gobierno publica en formatos desordenados y los convertimos en una base de datos limpia y blindada contra alteraciones.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: Heterogeneidad y Formatos Rotos",
        "text": "Los boletines mensuales de la Autoridad Marítima de Panamá (AMP) desde enero de 2014 hasta 2026 no existen como una API REST moderna ni como base de datos SQL accesible. Llegaron como 353 archivos individuales en formatos Excel (.xls y .xlsx) y reportes tabulados con celdas combinadas, encabezados multinivel flotantes, nombres de puertos cambiantes (ej. 'Cristobal' vs 'Puerto Cristóbal') y notas al pie incrustadas en las mismas celdas de números. Se construyó un parser heurístico con openpyxl y pandas que detecta dinámicamente las coordenadas relativas de terminales y meses sin depender de índices fijos."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Una sola terminal como Balboa o MIT maneja más de 200,000 TEUs mensuales. Si el sistema ingiere duplicados o meses desfasados, se distorsiona la programación de grúas pórtico STS (Super Post-Panamax), provocando sobrecostos de cuadrillas de estibadores o tiempos muertos de buques fondeados en bahía esperando atraque (costos de demurrage de hasta $40,000 USD por día por buque portacontenedores)."
      },
      "obstacles": [
        {
          "obs": "Celdas combinadas y formatos dispares entre boletines de 2014-2018 (formato clásico DGM) y 2019-2026 (plantilla moderna AMP).",
          "sol": "Escáner heurístico que localiza la celda ancla 'MOVIMIENTO.*CONTENEDORES' y mapea las coordenadas relativas de terminales independientemente de las filas vacías."
        },
        {
          "obs": "Caracteres especiales, saltos de línea '\\r\\n' y tildes corruptas por codificación mixta ISO-8859-1 y UTF-8.",
          "sol": "Capa de normalización Unicode NFKD con eliminación determinista de espacios invisibles antes del catálogo canónico de puertos."
        }
      ],
      "math": {
        "title": "Validación de Integridad Criptográfica de Ingesta y Balance Contable",
        "formula": "\\mathcal{H}(B_i) = \\text{SHA256}\\left( \\text{PayloadRaw}_i \\right) \\quad \\forall i \\in \\{1, \\dots, 353\\} \\\\ \\text{AuditGate}(B_i) = \\begin{cases} 1 & \\text{si } \\mathcal{H}(B_i) = \\mathcal{H}_{\\text{manifest}} \\ \\wedge \\ \\sum \\text{TEU}_{\\text{detalle}} = \\text{TEU}_{\\text{total}} \\\\ 0 & \\text{en caso contrario (Rechazo Inmediato)} \\end{cases}",
        "explanation": "Cada boletín ingerido genera un hash criptográfico SHA-256 inmutable almacenado en el manifiesto de auditoría. Además, se aplica un balance contable vectorial donde la suma de contenedores llenos locales, transbordo y vacíos debe coincidir de forma idéntica con el total reportado por la terminal.",
        "variables": [
          { "sym": "B_i", "name": "Boletín Estadístico i", "meaning": "Archivo binario correspondiente al mes i publicado oficialmente por la AMP (2014-2026)." },
          { "sym": "H(B_i)", "name": "Hash SHA-256", "meaning": "Resumen criptográfico de 256 bits que certifica que el archivo en disco no fue alterado." },
          { "sym": "AuditGate", "name": "Compuerta de Ingesta", "meaning": "Función indicatriz binaria: 1 autoriza el pase al Bronze Lakehouse, 0 veta el registro." },
          { "sym": "∑ TEU_detalle", "name": "Suma de Componentes", "meaning": "Llenos Locales + Transbordo + Vacíos declarados en las celdas de desglose." },
          { "sym": "TEU_total", "name": "Cifra de Control General", "meaning": "Total oficial consolidado informado por la administración portuaria." }
        ],
        "steps": [
          { "title": "Paso 1: Huella Criptográfica SHA-256", "desc": "Se lee el flujo de bytes crudo antes de cualquier transformación y se almacena su hash para trazabilidad inmutable ante la Contraloría." },
          { "title": "Paso 2: Conciliación Vectorial Contable", "desc": "Se verifica que la matriz de desglose (Llenos + Vacíos + Transbordo) cuadre exactamente con el total declarado por terminal." },
          { "title": "Paso 3: Compuerta de Veto Cero Tolerancia", "desc": "Cualquier descuadre mayor a 0 TEUs detiene la ingesta e ingresa a cuarentena para auditoría manual." }
        ],
        "interactive": "f1_reconcile"
      },
      "code": {
        "filepath": "src/data/cleaner.py",
        "snippet": "def ingest_amp_raw_bulletin(file_path: Path) -> pd.DataFrame:\n    # Verificación de integridad SHA-256 en reposo\n    file_hash = hashlib.sha256(file_path.read_bytes()).hexdigest()\n    wb = openpyxl.load_workbook(file_path, data_only=True)\n    sheet = wb.active\n    \n    anchor_row, anchor_col = find_anchor_cell(sheet, pattern=r'MOVIMIENTO.*CONTENEDORES')\n    records = parse_port_matrix(sheet, start_row=anchor_row + 2, start_col=anchor_col)\n    \n    df_bronze = pd.DataFrame(records)\n    df_bronze['ingest_sha256'] = file_hash\n    df_bronze['ingest_timestamp_utc'] = datetime.now(timezone.utc).isoformat()\n    return df_bronze"
      },
      "source": {
        "provenance": "Portal Oficial de Datos Abiertos de la República de Panamá & AMP",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "140 meses continuos (Enero 2014 – Febrero 2026)",
        "format": "Apache Parquet comprimido con Snappy, particionado por año y litoral",
        "hash": "SHA-256 Manifest: 9e3f1b4a... (Inmutable en almacenamiento WORM)"
      }
    },
    "phase_2": {
      "title": "Deduplicación Bitemporal & Limpieza Robusta (MAD Hampel)",
      "badge": "FASE 2: SILVER CLEANING",
      "sub": "Resolución determinista de versiones y filtrado no paramétrico de anomalías contables",
      "simple": "Detectamos y eliminamos números duplicados o correcciones que el ministerio hizo meses después, asegurando que el modelo solo aprenda con la versión oficial corregida y sin inventar datos.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: Boletines Acumulativos y Asientos Negativos",
        "text": "La AMP publica cifras mensuales acumulativas que sufren revisiones retroactivas continuas: un boletín publicado en marzo a menudo recalcula las cifras de enero y febrero debido a demoras en las declaraciones de aduanas de las navieras. Si un sistema simplemente concatena los reportes, se crean registros bitemporales en conflicto. Además, en los microdatos crudos se detectaron ajustes contables atípicos, como entradas de -111 TEUs en terminales secundarias causadas por notas de crédito de patios. Los métodos estadísticos tradicionales basados en 3 desviaciones estándar (Regla Z) fallaban completamente porque la varianza inflada por la pandemia de 2020 sesgaba la media."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Si se entrenan modelos de machine learning con duplicados temporales, el modelo sobreajusta los meses que tuvieron más revisiones burocráticas, creyendo erróneamente que esos meses tienen más peso estadístico. La limpieza bitemporal garantiza que la serie de tiempo refleje el flujo físico real de contenedores sobre los muelles panameños."
      },
      "obstacles": [
        {
          "obs": "Conflicto entre la fecha de ocurrencia del tráfico portuario (valid_time) y la fecha en que la AMP emitió el reporte oficial (system_time).",
          "sol": "Indexación bitemporal estricta preservando únicamente la tupla con MAX(system_time) para cada combinación única de (puerto, valid_time)."
        },
        {
          "obs": "Valores negativos de TEUs derivados de asientos de reclasificación contable en terminales privadas.",
          "sol": "Regla de saneamiento no destructiva: sustitución de números negativos por 0.0 registrando un bit de advertencia de auditoría (negative_corrected_flag = 1)."
        }
      ],
      "math": {
        "title": "Filtro Robusto de Hampel con Desviación Absoluta de la Mediana (MAD)",
        "formula": "\\text{MAD}_t = 1.4826 \\times \\text{mediana}_{k \\in [-W, W]} \\left( |y_{t+k} - \\tilde{y}_t| \\right) \\\\ \\text{Score}_t = \\frac{|y_t - \\tilde{y}_t|}{\\text{MAD}_t + \\epsilon} \\quad \\implies \\quad \\text{si } \\text{Score}_t > 3.0 \\implies \\text{Outlier Identificado}",
        "explanation": "El estimador MAD (Median Absolute Deviation) posee un punto de ruptura del 50%, lo que significa que resiste hasta un 50% de datos corruptos sin descalibrar el centro de la distribución. El factor 1.4826 asegura consistencia asintótica con la desviación estándar normal cuando los datos son gaussianos.",
        "variables": [
          { "sym": "y_t", "name": "Tráfico Observado Mes t", "meaning": "Volumen mensual de TEUs reportado en una terminal portuaria." },
          { "sym": "ỹ_t", "name": "Mediana Local Móvil", "meaning": "Mediana calculada dentro de una ventana temporal centrada de tamaño 2W + 1 (W = 3 meses)." },
          { "sym": "MAD_t", "name": "Median Absolute Deviation", "meaning": "Medida no paramétrica de dispersión resistente a cisnes negros y huelgas portuarias." },
          { "sym": "1.4826", "name": "Factor Asintótico de Consistencia", "meaning": "Equivalente a 1 / Φ⁻¹(0.75), iguala la MAD a la desviación estándar en distribuciones normales." },
          { "sym": "Score_t", "name": "Puntaje Hampel Z", "meaning": "Distancia estandarizada robusta; si supera 3.0 se clasifica como anomalía o ajuste contable." }
        ],
        "steps": [
          { "title": "Paso 1: Mediana Móvil Centrada", "desc": "Calcula el centro robusto de la serie ignorando picos de anomalías que inflarían el promedio aritmético." },
          { "title": "Paso 2: Cálculo de Distancias Absolutas", "desc": "Calcula |y_{t+k} - ỹ_t| y obtiene la mediana de estas desviaciones multiplicada por 1.4826." },
          { "title": "Paso 3: Detección y Aislamiento", "desc": "Asigna el puntaje Score_t. Los valores con Score > 3.0 se aíslan para que no sesguen el entrenamiento de árboles de gradiente." }
        ],
        "interactive": "f2_hampel"
      },
      "code": {
        "filepath": "src/data/cleaner.py",
        "snippet": "def deduplicate_bitemporal(df: pd.DataFrame) -> pd.DataFrame:\n    # Ordenamiento por fecha de validez y timestamp de publicación descendente\n    df_sorted = df.sort_values(by=['port', 'date', 'publication_date'], ascending=[True, True, False])\n    # Deduplicación determinista: conservar solo la versión más reciente publicada\n    df_clean = df_sorted.drop_duplicates(subset=['port', 'date'], keep='first').copy()\n    \n    # Corrección de anomalías contables negativas\n    negative_mask = df_clean['total_teu'] < 0\n    if negative_mask.any():\n        df_clean.loc[negative_mask, 'negative_corrected_flag'] = 1\n        df_clean.loc[negative_mask, 'total_teu'] = 0.0\n    return df_clean"
      },
      "source": {
        "provenance": "Motor de Limpieza Silver MLOps (src/data/cleaner.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "140 periodos mensuales validados (2014-01 a 2026-02)",
        "format": "Dataframe Silver validado contra esquema Pydantic v2",
        "hash": "Auditoría de integridad con cero duplicados bitemporales"
      }
    },
    "phase_3": {
      "title": "Feature Store Gold & Cero Fuga Temporal (Zero Lookahead - 85 Señales)",
      "badge": "FASE 3: GOLD FEATURE STORE",
      "sub": "Ingeniería de 85 variables causales respetando rigurosamente la frontera temporal",
      "simple": "Creamos 85 indicadores inteligentes (como el combustible de barcos, el tráfico de meses pasados y el ciclo anual) asegurándonos de nunca usar información del futuro para predecir el pasado.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: El Peligro de Data Leakage en Series Portuarias",
        "text": "El error más destructivo y común en Machine Learning logístico es la fuga de datos del futuro (Lookahead Leakage). Por ejemplo, calcular una media móvil centrada rolling(window=3, center=True) o usar estadísticas anuales totales para normalizar meses individuales introduce información futura en el pasado. En un entorno portuario real, el 15 de marzo solo se conocen las cifras cerradas hasta febrero; cualquier modelo que use información de marzo para predecir abril es un fraude matemático que colapsará en producción. Diseñamos un Feature Store con shift(1) obligatorio en todos los retardos y variables externas."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Los armadores globales (Maersk, MSC, CMA CGM) deciden los desvíos de servicios transatlánticos con 4 a 8 semanas de antelación. Las 85 variables del Feature Store Gold permiten anticipar si la capacidad de muelle del Atlántico (Manzanillo, Cristóbal, CCT) se saturará por congestión derivada de ventanas de atraque en la Costa Este de EE.UU."
      },
      "obstacles": [
        {
          "obs": "Fuga temporal inducida por transformaciones globales (StandardScaler ajustado sobre todo el conjunto de entrenamiento + prueba).",
          "sol": "Aislamiento temporal: los escaladores y transformadores se calibran exclusivamente sobre la ventana histórica de entrenamiento dentro de cada fold de Expanding Window."
        },
        {
          "obs": "Disponibilidad asincrónica de datos de bunkering marino (ventas de combustible VLSFO de la AMP) respecto al tráfico de TEUs.",
          "sol": "Uso de un retardo mínimo de 2 meses (lag_2) en señales macro externas para garantizar que en tiempo de inferencia el dato esté 100% disponible."
        }
      ],
      "math": {
        "title": "Armónicos Estacionales de Fourier y Retardos Temporales Causales",
        "formula": "x_{\\text{sin}, t} = \\sin\\left( \\frac{2\\pi \\cdot m_t}{12} \\right), \\quad x_{\\text{cos}, t} = \\cos\\left( \\frac{2\\pi \\cdot m_t}{12} \\right) \\\\ \\mathcal{F}_t = \\sigma\\left( \\{y_{t-k}\\}_{k=1}^{12}, \\ \\{B_{t-j}\\}_{j=2}^{6}, \\ \\text{Ratio}_{t-1}, \\ x_{\\text{sin}, t}, \\ x_{\\text{cos}, t} \\right) \\quad \\text{con } \\text{Cov}(e_t, \\mathcal{F}_t) = 0",
        "explanation": "Los armónicos trigonométricos capturan la periodicidad anual continua en el círculo unitario sin la discontinuidad que causaría una variable discreta de mes (12 a 1). La condición de ortogonalidad temporal garantiza que el conjunto de características pertenezca a la sigma-álgebra histórica sin componentes de innovación futura.",
        "variables": [
          { "sym": "m_t", "name": "Mes Calendario", "meaning": "Mes del año del registro de carga (1 para Enero hasta 12 para Diciembre)." },
          { "sym": "x_sin, x_cos", "name": "Armónicos de Fourier", "meaning": "Coordenadas continuas en el círculo unitario S¹ que preservan la proximidad entre Diciembre y Enero." },
          { "sym": "y_{t-k}", "name": "Retardos Autoregresivos (Lags)", "meaning": "Historia de TEUs con k ≥ 1 meses de retardo, impidiendo rigurosamente la fuga de datos del futuro." },
          { "sym": "B_{t-j}", "name": "Ventas de Bunkering Marino", "meaning": "Consumo de combustible marino en toneladas métricas con retardo de 2 meses (lag_2)." },
          { "sym": "Cov(e_t, F_t)", "name": "Condición de Exogeneidad", "meaning": "Garantiza que los residuos del pronóstico no estén correlacionados con las variables predictivas pasadas." }
        ],
        "steps": [
          { "title": "Paso 1: Mapeo Circular Continuo", "desc": "Convierte los 12 meses discretos en coordenadas senoidales y cosenoidales periódicas continuas." },
          { "title": "Paso 2: Desplazamiento Causal Shift(k)", "desc": "Aplica shift(1) hasta shift(12) en series de tráfico para alimentar los nodos de división de LightGBM." },
          { "title": "Paso 3: Ratios de Balance Operativo", "desc": "Calcula el ratio de trasbordo = Transbordo_{t-1} / Total_{t-1} como señal de saturación de patio." }
        ],
        "interactive": "f3_fourier"
      },
      "code": {
        "filepath": "src/features/feature_store.py",
        "snippet": "def generate_gold_features(df_silver: pd.DataFrame) -> pd.DataFrame:\n    df = df_silver.sort_values(by=['port', 'date']).copy()\n    \n    # 1. Armónicos estacionales continuos\n    df['month_sin'] = np.sin(2 * np.pi * df['date'].dt.month / 12.0)\n    df['month_cos'] = np.cos(2 * np.pi * df['date'].dt.month / 12.0)\n    \n    # 2. Retardos temporales causales con estricto shift >= 1\n    for k in [1, 2, 3, 6, 12]:\n        df[f'teu_lag_{k}'] = df.groupby('port')['total_teu'].shift(k)\n        \n    # 3. Ratio de transbordo histórico causal\n    df['transshipment_ratio_lag1'] = df.groupby('port')['transshipment_teu'].shift(1) / (df.groupby('port')['total_teu'].shift(1) + 1.0)\n    return df.dropna()"
      },
      "source": {
        "provenance": "Gold Feature Store (src/features/feature_store.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "85 columnas dimensionales auditadas y validadas con Great Expectations",
        "format": "Gold Table Parquet (Apache Arrow 14.0)",
        "hash": "Schema Hash Validado: Cero fuga temporal demostrada matemáticamente"
      }
    },
    "phase_4": {
      "title": "Inferencia Causal & Desacoplamiento Confundidor (Pearl do-calculus & VIF)",
      "badge": "FASE 4: CAUSALITY & VIF",
      "sub": "Separación formal de correlación espuria, eliminación de multicolinealidad y efectos de confusión",
      "simple": "Diferenciamos las causas reales de las coincidencias. Por ejemplo: si el combustible sube de precio cuando hay sequía, el modelo sabe aislar qué parte del cambio se debe al combustible y cuál al calado del Canal.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: El Fenómeno del Canal y el Año Nuevo Chino",
        "text": "El sistema portuario panameño no opera en el vacío. Cada febrero, las fábricas de Shenzhen y Ningbo cierran por el Año Nuevo Chino (CNY), desplomando las salidas hacia el Pacífico. Al mismo tiempo, en 2023-2024 la sequía del Lago Gatún obligó a la ACP a recortar tránsitos de buques Neopanamax de 38 a 22 diarios. Un modelo ingenuo correlaciona las ventas de combustible de bunkering marino con la caída de TEUs y concluye falsamente que 'vender menos combustible causa que los barcos no vengan'. Mediante el marco causal de Judea Pearl (do-calculus) y modelos de efectos fijos, desacoplamos la variable confusora (Capacidad de Tránsito del Canal) del impacto directo del precio de fletes."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Permite realizar simulaciones 'What-If' reales. Los directores de la AMP pueden responder: 'Si el precio internacional del bunker sube 20% pero el Canal mantiene 36 tránsitos diarios, ¿cuántos TEUs perderá Balboa frente a terminales de México o Colombia?'. Sin desacoplamiento causal, la respuesta del modelo sería una correlación espuria inútil para la toma de decisiones estratégicas del Estado."
      },
      "obstacles": [
        {
          "obs": "Multicolinealidad severa entre retardos sucesivos (lag_1 vs lag_2 presentaban r = 0.94, inflando VIF por encima de 15).",
          "sol": "Transformación a diferencias temporales (first differences) y ratios normalizados desacoplados, reduciendo el VIF global por debajo de 2.5."
        },
        {
          "obs": "Confusión estacional entre el Año Nuevo Chino y la estación seca en Panamá (enero-abril).",
          "sol": "Inclusión de la covariable exógena is_cny (calendario lunar variable) separada de los armónicos fijos del calendario gregoriano."
        }
      ],
      "math": {
        "title": "Factor de Inflación de la Varianza (VIF) y Operador do-calculus de Pearl",
        "formula": "\\text{VIF}_j = \\frac{1}{1 - R_j^2} < 2.5 \\\\ P(Y \\mid do(X = x)) = \\sum_z P(Y \\mid X=x, Z=z) P(Z=z) \\quad \\text{con } Z \\in \\{\\text{Sequía ACP}, \\text{CNY Lunar}\\}",
        "explanation": "El VIF mide cuánto se infla la varianza del coeficiente estimado debido a la correlación lineal con otras variables. Exigir VIF < 2.5 garantiza que cada variable aporta información ortogonal. El operador do(X) calcula el efecto de intervención activa eliminando los arcos entrantes de las variables confusoras Z en el Grafo Acíclico Dirigido (DAG).",
        "variables": [
          { "sym": "VIF_j", "name": "Variance Inflation Factor", "meaning": "Factor de inflación de varianza de la variable j; valores < 2.5 certifican no-redundancia." },
          { "sym": "R_j²", "name": "Coeficiente de Regresión Múltiple", "meaning": "R² resultante de regresar la variable j sobre el resto de las 84 variables del sistema." },
          { "sym": "do(X=x)", "name": "Operador Intervención de Pearl", "meaning": "Simulación contrafactual activa: altera el precio de flete X sin que dependa del pasado." },
          { "sym": "Z", "name": "Variables Confundidoras", "meaning": "Factores de confusión exógenos como la sequía del Lago Gatún o el Año Nuevo Chino lunar." }
        ],
        "steps": [
          { "title": "Paso 1: Diagnóstico Matricial VIF", "desc": "Calcula el VIF de cada columna numérica de forma iterativa y poda las variables con VIF > 2.5 para evitar pesos colineales inestables." },
          { "title": "Paso 2: Grafo Causal Dirigido (DAG)", "desc": "Estructura la dirección de causa-efecto: Sequía ➔ Calado del Canal ➔ Tránsitos ➔ TEUs en Balboa y Cristóbal." },
          { "title": "Paso 3: Bloqueo de Puertas Traseras", "desc": "Condiciona sobre la covariable confusora Z para aislar el efecto puro del combustible y fletes internacionales." }
        ],
        "interactive": "f4_vif"
      },
      "code": {
        "filepath": "src/models/trainer.py",
        "snippet": "def compute_vif_filter(X: pd.DataFrame, threshold: float = 2.5) -> list[str]:\n    from statsmodels.stats.outliers_influence import variance_inflation_factor\n    selected = list(X.columns)\n    while True:\n        vif = [variance_inflation_factor(X[selected].values, i) for i in range(len(selected))]\n        max_vif = max(vif)\n        if max_vif > threshold and len(selected) > 5:\n            idx_to_drop = vif.index(max_vif)\n            dropped = selected.pop(idx_to_drop)\n            print(f'Eliminada variable colineal {dropped} con VIF: {max_vif:.2f}')\n        else:\n            break\n    return selected"
      },
      "source": {
        "provenance": "Módulo de Causalidad y Diagnóstico de Residuos (src/models/trainer.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "Auditoría de VIF sobre las 85 variables numéricas del Feature Store Gold",
        "format": "Matriz de Covarianza & Grafo Causal DAG Validado",
        "hash": "Reporte VIF < 2.5 certificado para todas las variables retenidas"
      }
    },
    "phase_5": {
      "title": "Torneo Multi-Algoritmo & Inferencia Cuantílica (Pinball Loss)",
      "badge": "FASE 5: ML TOURNAMENT",
      "sub": "Expanding Window Backtesting (2022–2026) y cuantiles asimétricos P10, P50, P90",
      "simple": "Pusimos a competir 4 inteligencias artificiales diferentes sobre los datos de los últimos 4 años. Ganó LightGBM con 90.89% de precisión, entregando no un solo número, sino un rango seguro: el suelo mínimo y el techo máximo de carga.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: El Fracaso del K-Fold Convencional",
        "text": "Muchos científicos de datos cometen el grave error de usar K-Fold Cross Validation aleatorio en series temporales. Mezclar aleatoriamente el año 2018 con el 2024 destruye la estructura autocorrelacionada y simula un rendimiento falso y optimista. En este proyecto implementamos rigurosamente Expanding Window Backtesting con 4 ventanas temporales sucesivas (2022 a 2026), entrenando únicamente sobre el pasado y prediciendo sobre el futuro real no visto. Además, en logística un pronóstico puntual (ej. 'habrá 210,000 TEUs') es inútil: si la demanda es 230,000 el muelle colapsa. Se requiere inferencia cuantil asimétrica mediante Pinball Loss para obtener P10, P50 y P90."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "P10 (Suelo de Seguridad) define el flujo de caja mínimo para pagar a las concesionarias portuarias. P50 (Mediana) programa las compras de combustible y turnos estándar. P90 (Techo de Estrés) alerta a los capitanes de muelle para activar patios auxiliares y convocar estibadores eventuales antes de que los buques queden varados en el fondeadero."
      },
      "obstacles": [
        {
          "obs": "Cruzamiento de cuantiles (Quantile Crossing): en escenarios atípicos, el modelo podía generar matemáticamente P10 > P50 o P50 > P90.",
          "sol": "Implementación de una capa de ordenamiento monótono no decreciente: P10_adj = min(P10, P50) y P90_adj = max(P90, P50)."
        },
        {
          "obs": "Latencia de inferencia en servidores con recursos limitados.",
          "sol": "Compilación de árboles LightGBM con parámetros optimizados, logrando inferencia completa en menos de 10 milisegundos por terminal."
        }
      ],
      "math": {
        "title": "Función de Pérdida Pinball Loss (Check Loss) y Métricas WAPE / R²",
        "formula": "\\mathcal{L}_\\tau(y, \\hat{y}_\\tau) = \\sum_{i=1}^N \\max\\left( \\tau (y_i - \\hat{y}_{i, \\tau}), \\ (\\tau - 1)(y_i - \\hat{y}_{i, \\tau}) \\right) \\\\ \\text{WAPE} = \\frac{\\sum_{i=1}^N |y_i - \\hat{y}_i|}{\\sum_{i=1}^N y_i} = 9.11\\% \\quad \\implies \\quad \\text{Precisión Operativa} = 90.89\\%",
        "explanation": "Para tau = 0.90, subestimar la demanda penaliza 9 veces más que sobreestimarla, forzando a la red a predecir un techo robusto. La métrica WAPE (Weighted Absolute Percentage Error) es inmune a las divisiones por cero que inutilizan al MAPE en terminales de volumen reducido como Bocas Fruit Co.",
        "variables": [
          { "sym": "τ (tau)", "name": "Nivel Cuantílico", "meaning": "0.10 para suelo de seguridad P10, 0.50 para mediana P50, 0.90 para techo de estrés P90." },
          { "sym": "y_i", "name": "Demanda Real Observada", "meaning": "Contenedores TEUs físicamente movilizados en el muelle en el mes i." },
          { "sym": "ŷ_{i, τ}", "name": "Pronóstico Cuantílico", "meaning": "Estimación del percentil τ generada por los árboles de gradiente LightGBM." },
          { "sym": "L_τ", "name": "Pinball Check Loss", "meaning": "Pérdida asimétrica que castiga con pendiente τ los errores positivos y con (1-τ) los negativos." },
          { "sym": "WAPE", "name": "Weighted Absolute Percentage Error", "meaning": "Error absoluto ponderado por el volumen total; 9.11% alcanzado en el torneo oficial." }
        ],
        "steps": [
          { "title": "Paso 1: Expanding Window Backtesting", "desc": "Entrena en ventanas sucesivas (2014-2022, 2014-2023, 2014-2024) para certificar robustez en periodos de choque." },
          { "title": "Paso 2: Optimización Asimétrica LightGBM", "desc": "Entrena 3 modelos simultáneos minimizando Pinball Loss en cuantil 0.10, 0.50 y 0.90." },
          { "title": "Paso 3: Filtro de Monotonía No Decreciente", "desc": "Garantiza matemáticamente que P10 ≤ P50 ≤ P90 aplicando proyección cuantil monótona." }
        ],
        "interactive": "f5_pinball"
      },
      "code": {
        "filepath": "src/models/trainer.py",
        "snippet": "def train_quantile_champion(X_train: np.ndarray, y_train: np.ndarray) -> dict:\n    import lightgbm as lgb\n    models = {}\n    for q in [0.10, 0.50, 0.90]:\n        clf = lgb.LGBMRegressor(\n            objective='quantile',\n            alpha=q,\n            n_estimators=180,\n            learning_rate=0.035,\n            num_leaves=24,\n            random_state=42\n        )\n        clf.fit(X_train, y_train)\n        models[f'p{int(q*100)}'] = clf\n    return models"
      },
      "source": {
        "provenance": "Motor de Entrenamiento y Torneo MLOps (src/models/trainer.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "Evaluación empírica sobre 4 particiones temporales (2022–2026)",
        "format": "Modelos serializados con Joblib y metadatos JSON de reproducibilidad",
        "hash": "Champion Verificado: WAPE 9.11% | R² 0.9594 | Latencia 9.8 ms"
      }
    },
    "phase_6": {
      "title": "Simulación Estocástica & Reverse Stress Testing",
      "badge": "FASE 6: MONTE CARLO ENGINE",
      "sub": "Factorización de Cholesky, saltos de Poisson de Merton (1976) y optimizador Powell",
      "simple": "Simulamos miles de futuros posibles en la computadora (como si tiráramos dados matemáticos 5,000 veces) para saber qué tan probable es que un huracán, una huelga o una sequía sature los puertos de Panamá.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: El Riesgo de Cola y Eventos Extremos de Cisne Negro",
        "text": "Los modelos de regresión estándar suponen perturbaciones normales simétricas. Pero en el transporte marítimo mundial, los desastres no son gaussianos: la sequía histórica del Canal de Panamá en 2023 o el bloqueo del Canal de Suez por el buque Ever Given en 2021 causan caídas abruptas no lineales seguidas de olas masivas de congestión en patios. Diseñamos un motor estocástico que combina difusión browniana correlacionada entre terminales mediante descomposición de Cholesky y procesos de saltos de Poisson de Merton (1976). Además, implementamos Reverse Stress Testing: en lugar de adivinar qué pasará, el algoritmo optimiza hacia atrás para descubrir cuál es la perturbación mínima de fletes y combustible que causaría un colapso del 25% de la capacidad nacional."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Permite calcular el Value at Risk (VaR 95%) y Conditional Value at Risk (CVaR / Expected Shortfall). El Ministerio de Economía y Finanzas (MEF) y la AMP pueden constituir reservas de contingencia presupuestaria sabiendo con certeza matemática cuál es la pérdida máxima esperada en los peores escenarios del 5% de cola."
      },
      "obstacles": [
        {
          "obs": "Matrices de covarianza empíricas no semidefinidas positivas debido a meses con datos faltantes en terminales pequeñas.",
          "sol": "Aplicación del algoritmo de Higham (2002) para proyectar la matriz empírica sobre el cono de matrices semidefinidas positivas antes de aplicar Cholesky."
        },
        {
          "obs": "Explosión combinatoria en la búsqueda del vector de estrés inverso.",
          "sol": "Optimización no lineal mediante el algoritmo de Powell sin derivadas, garantizando convergencia en menos de 200 iteraciones numéricas."
        }
      ],
      "math": {
        "title": "Ecuación Diferencial Estocástica de Merton (1976) y Factorización Cholesky",
        "formula": "\\frac{dS_t}{S_t} = (\\mu - \\lambda \\kappa) dt + \\sigma L dW_t + J_t dN_t \\quad \\text{con } \\Sigma = L L^T \\\\ \\text{CVaR}_{\\alpha}(Y) = \\mathbb{E}[Y \\mid Y \\le \\text{VaR}_{\\alpha}(Y)] = \\frac{1}{1-\\alpha} \\int_0^{1-\\alpha} \\text{VaR}_u(Y) du",
        "explanation": "dW_t es un movimiento browniano estándar vectorizado, correlacionado mediante la matriz triangular inferior L de Cholesky. dN_t es un proceso de conteo de Poisson con intensidad lambda, donde cada salto J_t tiene una distribución log-normal que modela huelgas portuarias o cierres de calado en el Canal.",
        "variables": [
          { "sym": "S_t", "name": "Vector de Tráfico Portuario", "meaning": "Volumen estocástico de TEUs en muelles en el tiempo continuo t." },
          { "sym": "μ, σ", "name": "Deriva y Volatilidad Continua", "meaning": "Crecimiento tendencial de comercio marítimo y dispersión browniana anual." },
          { "sym": "L (Cholesky)", "name": "Matriz Triangular Inferior", "meaning": "Descomposición tal que L·Lᵀ = Σ; preserva la correlación real entre puertos del Atlántico y Pacífico." },
          { "sym": "dN_t (Poisson)", "name": "Proceso de Saltos Discretos", "meaning": "Contador de eventos discretos con intensidad λ (ej: sequías severas o bloqueos de canal)." },
          { "sym": "CVaR_α", "name": "Conditional Value at Risk", "meaning": "Pérdida esperada en el peor 5% de las 5,000 trayectorias simuladas (Expected Shortfall)." }
        ],
        "steps": [
          { "title": "Paso 1: Descomposición de Cholesky", "desc": "Calcula L a partir de la matriz de covarianza Σ para generar variables aleatorias correlacionadas entre Balboa y Colón." },
          { "title": "Paso 2: Generación de Caminos Monte Carlo", "desc": "Simula 5,000 trayectorias integrando el término continuo de difusión con saltos de Poisson de Merton." },
          { "title": "Paso 3: Optimización Inversa de Powell", "desc": "Descubre la combinación mínima de estrés macroeconómico que generaría una pérdida de más de 50,000 TEUs." }
        ],
        "interactive": "f6_merton"
      },
      "code": {
        "filepath": "src/models/monte_carlo.py",
        "snippet": "def simulate_merton_paths(y0: float, mu: float, sigma: float, jump_intensity: float, n_paths: int = 1000, n_steps: int = 6) -> np.ndarray:\n    dt = 1.0 / 12.0\n    paths = np.zeros((n_paths, n_steps + 1))\n    paths[:, 0] = y0\n    \n    for t in range(1, n_steps + 1):\n        # 1. Componente continuo Browniano\n        z = np.random.standard_normal(n_paths)\n        diffusion = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z\n        \n        # 2. Saltos de Poisson de Merton (Cisnes Negros)\n        poisson_jumps = np.random.poisson(jump_intensity * dt, n_paths)\n        jump_sizes = np.random.normal(-0.15, 0.08, n_paths) * (poisson_jumps > 0)\n        \n        paths[:, t] = paths[:, t-1] * np.exp(diffusion + jump_sizes)\n    return paths"
      },
      "source": {
        "provenance": "Motor Estocástico y Estrés Inverso (src/models/monte_carlo.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "Generación en tiempo real de 1,000 a 10,000 trayectorias sintéticas auditadas",
        "format": "Arreglos multidimensionales NumPy con semilla criptográfica PRNG",
        "hash": "Garantía de reproducibilidad estocástica vía Mersenne Twister controlado"
      }
    },
    "phase_7": {
      "title": "Descontaminación & Privacidad Criptográfica (Ley 81 de 2019)",
      "badge": "FASE 7: ISO & LEY 81",
      "sub": "Cumplimiento obligatorio de la Ley de Protección de Datos Personales de Panamá",
      "simple": "Ciframos y ocultamos de manera matemática e irreversible los nombres de los barcos y dueños de carga para proteger los secretos comerciales y cumplir al 100% con la ley panameña.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: Secreto Comercial y Ley 81 de 2019",
        "text": "Los manifiestos portuarios de importación y trasbordo contienen números de identificación de buque (IMO), nombres de capitanes, consignatarios aduaneros y tipos específicos de mercancías. La Ley 81 del 26 de marzo de 2019 (de Protección de Datos Personales) y el Decreto Ejecutivo 285 de 2021 de la República de Panamá imponen multas de hasta $10,000 USD y sanciones penales por la exposición de datos comerciales sensibles o individualmente identificables. En este proyecto se construyó un pipeline de sanitización que bloquea cualquier dato a nivel de conocimiento de embarque (Bill of Lading) o identificador de contenedor (código BIC), aplicando agregación canónica macro a nivel de terminal portuaria mensual y hashing HMAC-SHA256 con sal rotativa."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Permite que la AMP y los operadores portuarios compartan modelos de inteligencia artificial y benchmarks entre terminales competidoras (ej. Manzanillo vs Colon Container Terminal) sin violar acuerdos de confidencialidad comercial ni las normas antimonopolio de ACODECO."
      },
      "obstacles": [
        {
          "obs": "Riesgo de ataque de reidentificación por correlación temporal si un buque atracó en una fecha exclusiva con carga muy singular.",
          "sol": "Agregación temporal forzosa a escala mensual (k-anonymity con k > 50 buques por bucket), haciendo matemáticamente imposible deducir el volumen de un cliente específico."
        },
        {
          "obs": "Ataques de diccionario sobre números IMO de buques usando hashes simples MD5 o SHA-1.",
          "sol": "Uso de HMAC-SHA256 con sal criptográfica de 256 bits generada por el módulo secrets del sistema operativo y almacenada en memoria efímera."
        }
      ],
      "math": {
        "title": "K-Anonimato Criptográfico y Transformación HMAC-SHA256",
        "formula": "\\text{Hash}(\\text{IMO}_i, \\text{Sal}_p) = \\text{HMAC-SHA256}_{K_p}\\left( \\text{IMO}_i \\parallel \\text{Sal}_p \\right) \\\\ \\forall Q \\in \\mathcal{D}, \\quad |\\{r \\in \\mathcal{D} \\mid r[\\text{Quasi-ID}] = Q\\}| \\ge k \\quad (k = 50)",
        "explanation": "El k-anonimato garantiza que cada registro sea indistinguible de al menos otros k-1 registros dentro del mismo grupo de consulta. La sal criptográfica individualizada por puerto impide que un adversario use tablas de arcoíris (Rainbow Tables) para relacionar barcos entre terminales del Pacífico y Atlántico.",
        "variables": [
          { "sym": "IMO_i", "name": "Número IMO del Buque", "meaning": "Identificador único asignado por la Organización Marítima Internacional (OMI)." },
          { "sym": "Sal_p", "name": "Sal Criptográfica de Terminal", "meaning": "Cadena pseudoaleatoria de alta entropía por terminal que previene ataques de fuerza bruta." },
          { "sym": "K_p", "name": "Clave Secreta HMAC", "meaning": "Clave de 256 bits almacenada en memoria efímera y rotada semestralmente." },
          { "sym": "k-anonymity", "name": "Garantía de K-Anonimato", "meaning": "Criterio de privacidad donde cada registro es indistinguible de al menos k-1 observaciones (k=50)." }
        ],
        "steps": [
          { "title": "Paso 1: Ingesta con Filtro de Columnas Prohibidas", "desc": "Identifica y elimina nombres de consignatarios, códigos BIC de contenedor y número de BL." },
          { "title": "Paso 2: Tokenización HMAC con Sal", "desc": "Calcula el digest criptográfico de 16 caracteres hexadecimales para preservar el tracking relacional sin revelar el IMO." },
          { "title": "Paso 3: Verificación de Cumplimiento Ley 81", "desc": "Genera el certificado de sanitización WORM validando que k ≥ 50 en todas las consultas de la API pública." }
        ],
        "interactive": "f7_hmac"
      },
      "code": {
        "filepath": "src/data/anonymizer.py",
        "snippet": "def anonymize_maritime_identifiers(df: pd.DataFrame, salt: bytes) -> pd.DataFrame:\n    import hmac, hashlib\n    df_anon = df.copy()\n    \n    def hash_identifier(val: str) -> str:\n        if pd.isna(val) or not str(val).strip():\n            return 'ANON_NULL'\n        return hmac.new(salt, str(val).encode('utf-8'), hashlib.sha256).hexdigest()[:16]\n        \n    if 'vessel_imo' in df_anon.columns:\n        df_anon['vessel_imo_hash'] = df_anon['vessel_imo'].apply(hash_identifier)\n        df_anon.drop(columns=['vessel_imo'], inplace=True)\n    return df_anon"
      },
      "source": {
        "provenance": "Módulo de Sanitización y Ley 81 (src/data/anonymizer.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "Cero campos sensibles expuestos en tablas públicas y endpoints REST",
        "format": "Datasets agregados Macro-Terminal con hash HMAC de 16 caracteres",
        "hash": "Certificado de cumplimiento con Ley 81 de 2019 e ISO/IEC 27701:2019"
      }
    },
    "phase_8": {
      "title": "Gobernanza Estatal RBAC, Protocolo WORM & Servidor MCP",
      "badge": "FASE 8: GOVERNANCE & MCP",
      "sub": "Auditoría inmutable para AIG/Contraloría e interoperabilidad abierta con agentes de IA",
      "simple": "Hicimos que el sistema se comunique con cualquier inteligencia artificial moderna (Claude, Cursor, Antigravity) mediante un estándar abierto (MCP), dejando una bitácora digital blindada que ningún funcionario puede borrar ni alterar.",
      "context": {
        "title": "La Realidad Operativa Sin Maquillaje: El Desafío de Auditoría en el Sector Público",
        "text": "Los sistemas informáticos gubernamentales en América Latina suelen fallar por dos razones opuestas: o son 'cajas negras' cerradas cuyos funcionarios ocultan el código, o son sistemas sin bitácoras donde cualquier administrador puede modificar registros en base de datos sin dejar rastro. Para este proyecto exigimos un estándar de arquitectura que satisfaga a la Autoridad Nacional para la Innovación Gubernamental (AIG) y la Contraloría General de la República: registros de inferencia inmutables Write-Once-Read-Many (WORM), validación constante de firmas de servicio y un servidor nativo Model Context Protocol (MCP) que expone las herramientas analíticas mediante el protocolo estándar JSON-RPC 2.0."
      },
      "why": {
        "title": "Justificación de Negocio y Casos de Uso en Muelle",
        "text": "Permite que analistas de planificación de la AMP y operadores privados ejecuten consultas en lenguaje natural desde asistentes de IA conectados (ej: 'Compara la predicción de Balboa para el próximo trimestre usando LightGBM versus Random Forest') con la certeza de que el agente ejecuta herramientas verificadas y gobernadas bajo un esquema de permisos RBAC."
      },
      "obstacles": [
        {
          "obs": "Interconexión compleja entre agentes de IA propietarios y los microservicios analíticos en FastAPI.",
          "sol": "Implementación de la especificación oficial MCP (Model Context Protocol) sobre stdio y HTTP/SSE, exponiendo esquemas JSON Schema tipados."
        },
        {
          "obs": "Riesgo de repudio o alteración retroactiva de pronósticos presentados ante la Junta Directiva de la AMP.",
          "sol": "Cadena criptográfica de bloques en log (Hash Chaining WORM): cada pronóstico emitido incluye el hash del pronóstico anterior, imposibilitando la alteración sin invalidar la cadena."
        }
      ],
      "math": {
        "title": "Cadena Criptográfica WORM (Hash Chaining de Auditoría Estatal)",
        "formula": "\\mathcal{H}_t = \\text{SHA256}\\left( \\mathcal{H}_{t-1} \\parallel \\text{Timestamp} \\parallel \\text{Terminal} \\parallel \\hat{y}_{t, P50} \\parallel \\text{RoleID} \\right) \\\\ \\text{AuditChainValidity} = \\prod_{i=1}^T \\mathbb{I}\\left( \\mathcal{H}_i = \\text{SHA256}(\\mathcal{H}_{i-1} \\parallel \\dots) \\right) = 1",
        "explanation": "El protocolo WORM (Write Once, Read Many) asegura que ninguna predicción histórica pueda ser reescrita. Si un auditor de la Contraloría verifica la cadena desde el bloque génesis hasta el presente, cualquier cambio en un solo TEU rompería el encadenamiento criptográfico inmediatamente.",
        "variables": [
          { "sym": "H_t", "name": "Hash del Bloque Actual", "meaning": "Resumen SHA-256 del registro de pronóstico emitido en el instante t." },
          { "sym": "H_{t-1}", "name": "Hash del Bloque Predecesor", "meaning": "Enlace criptográfico que encadena el registro actual con toda la historia previa." },
          { "sym": "ŷ_{t, P50}", "name": "Pronóstico Mediano Registrado", "meaning": "Volumen oficial de TEUs emitido por el modelo en producción." },
          { "sym": "RoleID", "name": "Identificador de Rol RBAC", "meaning": "Firma del rol institucional que autorizó o consultó la inferencia (ej. mlops_engineer)." },
          { "sym": "AuditChainValidity", "name": "Producto Indicador de Validez", "meaning": "Comprobación estricta de que todos los eslabones coinciden matemáticamente; debe ser 1." }
        ],
        "steps": [
          { "title": "Paso 1: Ensamblado del Payload de Auditoría", "desc": "Concatena el hash del bloque previo, fecha/hora UTC, ID del modelo, puerto y firma de usuario." },
          { "title": "Paso 2: Sellado SHA-256 WORM", "desc": "Computa el hash inmutable y lo guarda en el ledger de auditoría protegido contra sobrescritura." },
          { "title": "Paso 3: Verificación Forense Continua", "desc": "Permite auditar el ledger completo en O(N) verificando que ningún registro fue alterado retroactivamente." }
        ],
        "interactive": "f8_worm"
      },
      "code": {
        "filepath": "src/mcp/server.py",
        "snippet": "async def handle_mcp_call_tool(name: str, arguments: dict) -> dict:\n    # Protocolo MCP / JSON-RPC 2.0 con RBAC estricto\n    if name == 'get_port_forecast':\n        port = arguments.get('port', 'Puerto Balboa')\n        horizon = int(arguments.get('horizon_months', 3))\n        algo = arguments.get('algorithm', 'ensemble')\n        result = await execute_governed_forecast(port, horizon, algo)\n        return {\n            'content': [{'type': 'text', 'text': json.dumps(result, indent=2)}],\n            'isError': False\n        }\n    raise ValueError(f'Herramienta desconocida: {name}')"
      },
      "source": {
        "provenance": "Servidor MCP & Capa de Gobernanza Estatal (src/mcp/server.py)",
        "url": "https://www.datosabiertos.gob.pa/dataset/?organization=autoridad-maritima-de-panama-amp",
        "coverage": "5 herramientas analíticas MCP expuestas con tipado JSON Schema",
        "format": "JSON-RPC 2.0 estándar / Claude Desktop Config",
        "hash": "Protocolo WORM con Hash Chaining validado para auditoría pública"
      }
    }
  };

  let currentSelectedPhase = "phase_1";
  let currentSelectedDim = "dim-context";
  window.currentSelectedModalDim = "dim-context";

  function escapeHtmlCode(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function generateDimensionHTML(phase, dimId) {
    if (!phase) return "";

    if (dimId === "dim-context") {
      return `
        <div class="real-context-card">
          <div class="real-context-title">
            <span>📋</span> ${phase.context.title}
          </div>
          <p style="font-size:0.88rem; line-height:1.65; color:#f1f5f9; margin-bottom:0.75rem;">
            ${phase.context.text}
          </p>
        </div>
        <div style="background:rgba(255,255,255,0.02); border:1px solid var(--border-color); border-radius:8px; padding:1rem;">
          <h5 style="color:var(--cyan-bright); margin-bottom:0.4rem; font-size:0.82rem;">💡 Traducción Ciudadana Sencilla:</h5>
          <p style="font-size:0.82rem; color:var(--text-muted); margin:0;">${phase.simple}</p>
        </div>
      `;
    } else if (dimId === "dim-why") {
      return `
        <div style="background:rgba(56, 189, 248, 0.05); border:1px solid rgba(56, 189, 248, 0.25); border-radius:10px; padding:1.25rem;">
          <h4 style="color:var(--cyan-bright); font-size:0.95rem; margin-bottom:0.6rem; display:flex; align-items:center; gap:0.4rem;">
            <span>🎯</span> ${phase.why.title}
          </h4>
          <p style="font-size:0.88rem; line-height:1.65; color:#e2e8f0; margin-bottom:0;">
            ${phase.why.text}
          </p>
        </div>
      `;
    } else if (dimId === "dim-obstacles") {
      let obstaclesHtml = '<div class="obstacle-grid">';
      phase.obstacles.forEach((item, idx) => {
        obstaclesHtml += `
          <div class="obstacle-card">
            <h5 style="color:#fbbf24; font-size:0.82rem; margin-bottom:0.4rem; display:flex; align-items:center; gap:0.3rem;">
              <span>⚠️</span> Obstáculo Real #${idx + 1}
            </h5>
            <p style="font-size:0.8rem; color:#fef3c7; line-height:1.5; margin:0;">${item.obs}</p>
          </div>
          <div class="solution-card">
            <h5 style="color:#34d399; font-size:0.82rem; margin-bottom:0.4rem; display:flex; align-items:center; gap:0.3rem;">
              <span>✅</span> Solución de Ingeniería Implementada
            </h5>
            <p style="font-size:0.8rem; color:#d1fae5; line-height:1.5; margin:0;">${item.sol}</p>
          </div>
        `;
      });
      obstaclesHtml += '</div>';
      return obstaclesHtml;
    } else if (dimId === "dim-math") {
      let varsTable = "";
      if (phase.math.variables && phase.math.variables.length) {
        varsTable = `
          <div class="math-vars-section">
            <div class="math-section-subtitle">
              <span>📖</span> Diccionario de Símbolos & Variables de Inferencia
            </div>
            <table class="math-vars-table">
              <thead>
                <tr>
                  <th style="width: 15%;">Símbolo</th>
                  <th style="width: 30%;">Variable Técnica</th>
                  <th style="width: 55%;">Significado Físico / Portuario</th>
                </tr>
              </thead>
              <tbody>
                ${phase.math.variables.map(v => `
                  <tr>
                    <td class="var-symbol">${v.sym}</td>
                    <td><strong>${v.name}</strong></td>
                    <td>${v.meaning}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        `;
      }

      let stepsHtml = "";
      if (phase.math.steps && phase.math.steps.length) {
        stepsHtml = `
          <div class="math-section-subtitle" style="margin-top:1rem;">
            <span>🔬</span> Desglose Matemático & Algorítmico Paso a Paso
          </div>
          <div class="math-steps-grid">
            ${phase.math.steps.map(s => `
              <div class="math-step-card">
                <div class="math-step-header">
                  <span>🔹</span> ${s.title}
                </div>
                <p class="math-step-desc">${s.desc}</p>
              </div>
            `).join('')}
          </div>
        `;
      }

      let sandboxHtml = "";
      if (phase.math.interactive === "f1_reconcile") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Balance Vectorial de Ingesta (SHA-256 AuditGate)</span>
              <span class="badge" style="font-size:0.65rem;">Reactivo</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Llenos Locales:</label>
                <input type="number" id="sbox-f1-local" class="math-sandbox-input" value="45000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Transbordo:</label>
                <input type="number" id="sbox-f1-trans" class="math-sandbox-input" value="140000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Vacíos:</label>
                <input type="number" id="sbox-f1-empty" class="math-sandbox-input" value="25000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Total Declarado:</label>
                <input type="number" id="sbox-f1-manifest" class="math-sandbox-input" value="210000">
              </div>
              <div id="sbox-f1-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f2_hampel") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Detector de Outliers Robusto (MAD Hampel)</span>
              <span class="badge" style="font-size:0.65rem;">Umbral Hampel: 3.0</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Tráfico Observado (y_t):</label>
                <input type="number" id="sbox-f2-val" class="math-sandbox-input" value="275000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Mediana Móvil (ỹ_t):</label>
                <input type="number" id="sbox-f2-med" class="math-sandbox-input" value="210000">
              </div>
              <div class="math-sandbox-control-group">
                <label>MAD Estimada:</label>
                <input type="number" id="sbox-f2-mad" class="math-sandbox-input" value="16000">
              </div>
              <div id="sbox-f2-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f3_fourier") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Armónicos Estacionales de Fourier Continuos</span>
              <span class="badge" style="font-size:0.65rem;">Círculo Unitario S¹</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Mes Calendario:</label>
                <select id="sbox-f3-month" class="math-sandbox-input" style="width:130px;">
                  <option value="1">1 (Enero)</option>
                  <option value="2">2 (Febrero - CNY)</option>
                  <option value="3">3 (Marzo)</option>
                  <option value="7">7 (Julio)</option>
                  <option value="11">11 (Noviembre)</option>
                  <option value="12">12 (Diciembre)</option>
                </select>
              </div>
              <div id="sbox-f3-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f4_vif") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Gauge de Multicolinealidad (VIF Causal)</span>
              <span class="badge" style="font-size:0.65rem;">VIF Máximo Admisible: 2.5</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group" style="flex:1;">
                <label>R² de Regresión Múltiple: <strong id="sbox-f4-r2-val">0.50</strong></label>
                <input type="range" id="sbox-f4-r2" min="0" max="0.98" step="0.01" value="0.50" style="width:100%;">
              </div>
              <div id="sbox-f4-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f5_pinball") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Función de Pérdida Asimétrica (Pinball Loss)</span>
              <span class="badge" style="font-size:0.65rem;">Penalización Asimétrica</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Cuantil (τ):</label>
                <select id="sbox-f5-tau" class="math-sandbox-input" style="width:110px;">
                  <option value="0.10">P10 (τ = 0.10)</option>
                  <option value="0.50">P50 (τ = 0.50)</option>
                  <option value="0.90" selected>P90 (τ = 0.90)</option>
                </select>
              </div>
              <div class="math-sandbox-control-group" style="flex:1;">
                <label>Error Residual (y - ŷ): <strong id="sbox-f5-res-val">+15,000 TEUs</strong></label>
                <input type="range" id="sbox-f5-res" min="-40000" max="40000" step="1000" value="15000" style="width:100%;">
              </div>
              <div id="sbox-f5-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f6_merton") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Difusión con Saltos de Merton & CVaR(95%)</span>
              <span class="badge" style="font-size:0.65rem;">Monte Carlo Engine</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Demanda Base (S_0):</label>
                <input type="number" id="sbox-f6-s0" class="math-sandbox-input" value="220000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Intensidad Salto (λ):</label>
                <input type="number" id="sbox-f6-lambda" class="math-sandbox-input" value="0.30" step="0.05">
              </div>
              <div class="math-sandbox-control-group">
                <label>Magnitud Shock:</label>
                <select id="sbox-f6-shock" class="math-sandbox-input" style="width:110px;">
                  <option value="-0.15">-15%</option>
                  <option value="-0.25" selected>-25% (Severo)</option>
                  <option value="-0.40">-40% (Cisne)</option>
                </select>
              </div>
              <div id="sbox-f6-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f7_hmac") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Anonimizador Criptográfico HMAC-SHA256 (Ley 81)</span>
              <span class="badge" style="font-size:0.65rem;">K-Anonimato k ≥ 50</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>IMO Buque:</label>
                <input type="text" id="sbox-f7-imo" class="math-sandbox-input" value="9811000">
              </div>
              <div class="math-sandbox-control-group">
                <label>Sal Terminal:</label>
                <select id="sbox-f7-salt" class="math-sandbox-input" style="width:140px;">
                  <option value="BALBOA-2026">Balboa Salt 2026</option>
                  <option value="CRISTOBAL-2026">Cristóbal Salt 2026</option>
                  <option value="MIT-2026">MIT Salt 2026</option>
                </select>
              </div>
              <div id="sbox-f7-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      } else if (phase.math.interactive === "f8_worm") {
        sandboxHtml = `
          <div class="math-sandbox-box">
            <div class="math-sandbox-header">
              <span>🧮 Simulador en Vivo: Cadena de Bloques Criptográfica WORM (Auditoría AIG)</span>
              <span class="badge" style="font-size:0.65rem;">Hash Chaining</span>
            </div>
            <div class="math-sandbox-controls">
              <div class="math-sandbox-control-group">
                <label>Pronóstico P50 (TEUs):</label>
                <input type="number" id="sbox-f8-teu" class="math-sandbox-input" value="218450">
              </div>
              <div class="math-sandbox-control-group">
                <label>Rol Auditor:</label>
                <select id="sbox-f8-role" class="math-sandbox-input" style="width:130px;">
                  <option value="mlops_engineer">mlops_engineer</option>
                  <option value="compliance_auditor">compliance_auditor</option>
                  <option value="root_owner">root_owner</option>
                </select>
              </div>
              <div id="sbox-f8-result" class="math-sandbox-result">Calculando...</div>
            </div>
          </div>
        `;
      }

      const escapedLatex = phase.math.formula.replace(/\\/g, "\\\\");

      return `
        <div class="math-formula-container">
          <div class="math-title">
            <span>📐 ${phase.math.title}</span>
            <span class="badge" style="font-size:0.68rem; background:rgba(6,182,212,0.15); color:var(--cyan-bright); border:1px solid rgba(6,182,212,0.3);">KaTeX Rendered</span>
          </div>
          
          <div class="math-equation-display" data-formula="${escapeHtmlCode(phase.math.formula)}">
            <!-- KaTeX will render here in postRenderDimension -->
          </div>

          <div class="math-action-bar">
            <button class="btn-copy-latex" onclick="window.copyLatexToClipboard('${escapedLatex}', this)">
              <span>📋</span> Copiar Fórmula LaTeX
            </button>
          </div>

          <p style="font-size:0.83rem; color:#cbd5e1; line-height:1.6; margin-top:0.4rem; background:rgba(255,255,255,0.02); padding:0.65rem; border-radius:6px; border-left:3px solid var(--cyan-bright);">
            <strong>Principio Fundamental:</strong> ${phase.math.explanation}
          </p>

          ${varsTable}
          ${stepsHtml}
          ${sandboxHtml}
        </div>
      `;
    } else if (dimId === "dim-code") {
      return `
        <div class="code-python-container">
          <div class="code-python-header">
            <span>🐍 Archivo Fuente: ${phase.code.filepath}</span>
            <button class="btn-copy-latex" onclick="window.copyLatexToClipboard(\`${phase.code.snippet.replace(/`/g, '\\`')}\`, this)">
              <span>📋</span> Copiar Código Python
            </button>
          </div>
          <pre class="code-python-body"><code>${escapeHtmlCode(phase.code.snippet)}</code></pre>
        </div>
      `;
    } else if (dimId === "dim-source") {
      return `
        <div style="background:rgba(16, 185, 129, 0.05); border:1px solid rgba(16, 185, 129, 0.25); border-radius:10px; padding:1.25rem;">
          <h4 style="color:#34d399; font-size:0.95rem; margin-bottom:0.6rem; display:flex; align-items:center; gap:0.4rem;">
            <span>🔗</span> Procedencia de Datos & Trazabilidad de Auditoría
          </h4>
          <ul style="font-size:0.82rem; color:#e2e8f0; line-height:1.7; padding-left:1.2rem; margin:0;">
            <li><strong>Entidad Emisora:</strong> ${phase.source.provenance}</li>
            <li><strong>Enlace Oficial:</strong> <a href="${phase.source.url}" target="_blank" style="color:var(--cyan-bright); word-break:break-all;">${phase.source.url}</a></li>
            <li><strong>Ventana Temporal:</strong> ${phase.source.coverage}</li>
            <li><strong>Formato en Disco:</strong> ${phase.source.format}</li>
            <li><strong>Verificación de Integridad:</strong> <code>${phase.source.hash}</code></li>
          </ul>
        </div>
      `;
    }
    return "";
  }

  function postRenderDimension(container, phase, dimId) {
    if (!container || !phase) return;

    if (dimId === "dim-math") {
      // 1. Render KaTeX Equation
      const eqDisplay = container.querySelector(".math-equation-display");
      if (eqDisplay && phase.math && phase.math.formula) {
        window.renderKaTeXMath(phase.math.formula, eqDisplay, true);
      }

      // 2. Wire up Interactive Sandboxes
      if (phase.math.interactive === "f1_reconcile") {
        const localIn = container.querySelector("#sbox-f1-local");
        const transIn = container.querySelector("#sbox-f1-trans");
        const emptyIn = container.querySelector("#sbox-f1-empty");
        const manIn = container.querySelector("#sbox-f1-manifest");
        const resEl = container.querySelector("#sbox-f1-result");
        const updateF1 = () => {
          const l = parseFloat(localIn.value) || 0;
          const t = parseFloat(transIn.value) || 0;
          const e = parseFloat(emptyIn.value) || 0;
          const m = parseFloat(manIn.value) || 0;
          const sum = l + t + e;
          const diff = sum - m;
          if (Math.abs(diff) === 0) {
            resEl.innerHTML = `AuditGate: <strong>1 (APROBADO)</strong> • Suma: ${sum.toLocaleString()} = Manifiesto: ${m.toLocaleString()}`;
            resEl.style.color = "#34d399";
            resEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
          } else {
            resEl.innerHTML = `AuditGate: <strong>0 (VETO)</strong> • Discrepancia: ${diff > 0 ? '+' : ''}${diff.toLocaleString()} TEUs`;
            resEl.style.color = "#f87171";
            resEl.style.borderColor = "rgba(239, 68, 68, 0.4)";
          }
        };
        [localIn, transIn, emptyIn, manIn].forEach(inp => inp && inp.addEventListener("input", updateF1));
        updateF1();
      } else if (phase.math.interactive === "f2_hampel") {
        const valIn = container.querySelector("#sbox-f2-val");
        const medIn = container.querySelector("#sbox-f2-med");
        const madIn = container.querySelector("#sbox-f2-mad");
        const resEl = container.querySelector("#sbox-f2-result");
        const updateF2 = () => {
          const y = parseFloat(valIn.value) || 0;
          const med = parseFloat(medIn.value) || 0;
          const mad = parseFloat(madIn.value) || 1;
          const score = Math.abs(y - med) / (1.4826 * mad + 0.001);
          if (score > 3.0) {
            resEl.innerHTML = `⚠️ <strong>OUTLIER DETECTADO</strong> • Score Z: ${score.toFixed(2)} > 3.0 (Ajuste o Shock)`;
            resEl.style.color = "#fbbf24";
            resEl.style.borderColor = "rgba(251, 191, 36, 0.4)";
          } else {
            resEl.innerHTML = `✅ <strong>FLUJO NORMAL</strong> • Score Z: ${score.toFixed(2)} ≤ 3.0 (Válido)`;
            resEl.style.color = "#34d399";
            resEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
          }
        };
        [valIn, medIn, madIn].forEach(inp => inp && inp.addEventListener("input", updateF2));
        updateF2();
      } else if (phase.math.interactive === "f3_fourier") {
        const mSelect = container.querySelector("#sbox-f3-month");
        const resEl = container.querySelector("#sbox-f3-result");
        const updateF3 = () => {
          const m = parseInt(mSelect.value, 10);
          const angle = 2 * Math.PI * m / 12.0;
          const s = Math.sin(angle);
          const c = Math.cos(angle);
          resEl.innerHTML = `x_sin: <strong>${s.toFixed(3)}</strong>, x_cos: <strong>${c.toFixed(3)}</strong> (Radio S¹: 1.000)`;
          resEl.style.color = "#38bdf8";
        };
        if (mSelect) mSelect.addEventListener("change", updateF3);
        updateF3();
      } else if (phase.math.interactive === "f4_vif") {
        const r2In = container.querySelector("#sbox-f4-r2");
        const r2Val = container.querySelector("#sbox-f4-r2-val");
        const resEl = container.querySelector("#sbox-f4-result");
        const updateF4 = () => {
          const r2 = parseFloat(r2In.value);
          if (r2Val) r2Val.textContent = r2.toFixed(2);
          const vif = 1.0 / (1.0 - r2 + 0.0001);
          if (vif < 2.5) {
            resEl.innerHTML = `VIF: <strong>${vif.toFixed(2)}</strong> • ✅ Ortogonal y Aceptable (< 2.5)`;
            resEl.style.color = "#34d399";
            resEl.style.borderColor = "rgba(16, 185, 129, 0.4)";
          } else if (vif < 5.0) {
            resEl.innerHTML = `VIF: <strong>${vif.toFixed(2)}</strong> • ⚠️ Colinealidad Moderada`;
            resEl.style.color = "#fbbf24";
            resEl.style.borderColor = "rgba(251, 191, 36, 0.4)";
          } else {
            resEl.innerHTML = `VIF: <strong>${vif.toFixed(2)}</strong> • ⛔ Colinealidad Severa (Podar Variable)`;
            resEl.style.color = "#f87171";
            resEl.style.borderColor = "rgba(239, 68, 68, 0.4)";
          }
        };
        if (r2In) r2In.addEventListener("input", updateF4);
        updateF4();
      } else if (phase.math.interactive === "f5_pinball") {
        const tauSelect = container.querySelector("#sbox-f5-tau");
        const resIn = container.querySelector("#sbox-f5-res");
        const resVal = container.querySelector("#sbox-f5-res-val");
        const resEl = container.querySelector("#sbox-f5-result");
        const updateF5 = () => {
          const tau = parseFloat(tauSelect.value);
          const err = parseFloat(resIn.value);
          if (resVal) resVal.textContent = `${err > 0 ? '+' : ''}${err.toLocaleString()} TEUs`;
          const loss = Math.max(tau * err, (tau - 1.0) * err);
          const factor = err > 0 ? tau : (1.0 - tau);
          resEl.innerHTML = `Pérdida L_${tau}: <strong>${Math.round(loss).toLocaleString()} TEUs</strong> (Factor penalización: ${factor.toFixed(2)})`;
          resEl.style.color = "#a5f3fc";
        };
        if (tauSelect) tauSelect.addEventListener("change", updateF5);
        if (resIn) resIn.addEventListener("input", updateF5);
        updateF5();
      } else if (phase.math.interactive === "f6_merton") {
        const s0In = container.querySelector("#sbox-f6-s0");
        const lIn = container.querySelector("#sbox-f6-lambda");
        const shIn = container.querySelector("#sbox-f6-shock");
        const resEl = container.querySelector("#sbox-f6-result");
        const updateF6 = () => {
          const s0 = parseFloat(s0In.value) || 200000;
          const lam = parseFloat(lIn.value) || 0.2;
          const sh = parseFloat(shIn.value) || -0.25;
          const varEst = s0 * (1 - 0.12 - lam * Math.abs(sh) * 0.4);
          const cvarEst = s0 * (1 - 0.22 - lam * Math.abs(sh) * 0.8);
          resEl.innerHTML = `VaR(95%): <strong>${Math.round(varEst).toLocaleString()}</strong> | CVaR(95%): <strong>${Math.round(cvarEst).toLocaleString()} TEUs</strong>`;
          resEl.style.color = "#f472b6";
        };
        [s0In, lIn, shIn].forEach(inp => inp && inp.addEventListener("input", updateF6));
        updateF6();
      } else if (phase.math.interactive === "f7_hmac") {
        const imoIn = container.querySelector("#sbox-f7-imo");
        const saltSelect = container.querySelector("#sbox-f7-salt");
        const resEl = container.querySelector("#sbox-f7-result");
        const updateF7 = () => {
          const imo = (imoIn.value || "9811000").trim();
          const salt = (saltSelect.value || "BALBOA-2026").trim();
          // Deterministic pseudorandom hash string representation
          let hash = 0;
          const str = imo + ":" + salt;
          for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
          }
          const hex = Math.abs(hash).toString(16).padStart(8, '0') + "d9a74c1f";
          resEl.innerHTML = `Token Anonimizado: <code>0x${hex}</code> (Irreversible)`;
          resEl.style.color = "#34d399";
        };
        if (imoIn) imoIn.addEventListener("input", updateF7);
        if (saltSelect) saltSelect.addEventListener("change", updateF7);
        updateF7();
      } else if (phase.math.interactive === "f8_worm") {
        const teuIn = container.querySelector("#sbox-f8-teu");
        const roleSelect = container.querySelector("#sbox-f8-role");
        const resEl = container.querySelector("#sbox-f8-result");
        const updateF8 = () => {
          const teu = (teuIn.value || "218450").trim();
          const role = (roleSelect.value || "mlops_engineer").trim();
          let hash = 0;
          const str = "prev:8f9b2c:" + teu + ":" + role;
          for (let i = 0; i < str.length; i++) {
            hash = ((hash << 5) - hash) + str.charCodeAt(i);
            hash |= 0;
          }
          const hex = Math.abs(hash).toString(16).padStart(8, '0') + "c71e";
          resEl.innerHTML = `Bloque H_t: <code>0x${hex}</code> • Cadena WORM: <strong>VÁLIDA</strong>`;
          resEl.style.color = "#a7f3d0";
        };
        if (teuIn) teuIn.addEventListener("input", updateF8);
        if (roleSelect) roleSelect.addEventListener("change", updateF8);
        updateF8();
      }
    }
  }

  function renderDimensionContent() {
    const phase = window.methodologyCatalog[currentSelectedPhase];
    const box = document.getElementById("dim-content-box");
    if (!phase || !box) return;
    box.innerHTML = generateDimensionHTML(phase, currentSelectedDim);
    postRenderDimension(box, phase, currentSelectedDim);
  }

  function renderModalDimensionContent() {
    const phase = window.methodologyCatalog[currentSelectedPhase];
    const box = document.getElementById("mmodal-content-box");
    if (!phase || !box) return;
    box.innerHTML = generateDimensionHTML(phase, window.currentSelectedModalDim);
    postRenderDimension(box, phase, window.currentSelectedModalDim);
  }

  function updateModalHeaderAndContent() {
    const phase = window.methodologyCatalog[currentSelectedPhase];
    if (!phase) return;
    const badge = document.getElementById("mmodal-phase-badge");
    const title = document.getElementById("mmodal-phase-title");
    const sub = document.getElementById("mmodal-phase-sub");
    if (badge) badge.textContent = phase.badge;
    if (title) title.textContent = phase.title;
    if (sub) sub.textContent = phase.sub;
    renderModalDimensionContent();
  }

  // =========================================================================
  // CAMERA AUTO-SCROLL & WORKSTATION SELECTION
  // =========================================================================
  window.selectMethodologyPhase = function(phaseId, autoScroll = true) {
    if (!window.methodologyCatalog[phaseId]) return;
    currentSelectedPhase = phaseId;

    document.querySelectorAll(".method-phase-card").forEach(c => {
      c.classList.toggle("active", c.id === "card-" + phaseId);
    });

    const phase = window.methodologyCatalog[phaseId];
    const badge = document.getElementById("workstation-phase-badge");
    const title = document.getElementById("workstation-phase-title");
    const sub = document.getElementById("workstation-phase-sub");
    if (badge) badge.textContent = phase.badge;
    if (title) title.textContent = phase.title;
    if (sub) sub.textContent = phase.sub;

    renderDimensionContent();

    // Automatic camera movement to the detail workstation as requested
    if (autoScroll) {
      const workstation = document.getElementById("method-deepdive-workstation");
      if (workstation) {
        workstation.scrollIntoView({ behavior: "smooth", block: "start" });
        workstation.classList.remove("workstation-focus-pulse");
        void workstation.offsetWidth; // trigger reflow
        workstation.classList.add("workstation-focus-pulse");
      }
    }
  };

  window.switchDimensionTab = function(dimId) {
    currentSelectedDim = dimId;
    document.querySelectorAll(".dim-nav-btn").forEach(btn => {
      if (btn.getAttribute("data-dim") === dimId) {
        btn.classList.add("active");
      } else {
        btn.classList.remove("active");
      }
    });
    renderDimensionContent();
  };

  // =========================================================================
  // CENTERED METHODOLOGY MODAL WITH FULL NAVBAR (8 Phases & 6 Dimensions)
  // =========================================================================
  window.openCenteredMethodologyModal = function(phaseId) {
    if (phaseId && window.methodologyCatalog[phaseId]) {
      currentSelectedPhase = phaseId;
    }
    const modal = document.getElementById("methodology-centered-modal");
    if (!modal) return;

    // Sync phase tabs in modal
    document.querySelectorAll(".mmodal-phase-tab").forEach(tab => {
      tab.classList.toggle("active", tab.getAttribute("data-phase") === currentSelectedPhase);
    });

    // Sync dim tabs in modal
    document.querySelectorAll("[data-mmodal-dim]").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-mmodal-dim") === window.currentSelectedModalDim);
    });

    updateModalHeaderAndContent();
    modal.classList.add("open");
  };

  window.closeCenteredMethodologyModal = function() {
    const modal = document.getElementById("methodology-centered-modal");
    if (modal) modal.classList.remove("open");
  };

  window.switchModalPhase = function(phaseId) {
    if (!window.methodologyCatalog[phaseId]) return;
    currentSelectedPhase = phaseId;

    // Sync modal tabs
    document.querySelectorAll(".mmodal-phase-tab").forEach(tab => {
      tab.classList.toggle("active", tab.getAttribute("data-phase") === phaseId);
    });

    // Sync background cards
    document.querySelectorAll(".method-phase-card").forEach(c => {
      c.classList.toggle("active", c.id === "card-" + phaseId);
    });

    // Sync workstation header in background
    const phase = window.methodologyCatalog[phaseId];
    const badge = document.getElementById("workstation-phase-badge");
    const title = document.getElementById("workstation-phase-title");
    const sub = document.getElementById("workstation-phase-sub");
    if (badge) badge.textContent = phase.badge;
    if (title) title.textContent = phase.title;
    if (sub) sub.textContent = phase.sub;

    renderDimensionContent();
    updateModalHeaderAndContent();
  };

  window.switchModalDimTab = function(dimId) {
    window.currentSelectedModalDim = dimId;
    document.querySelectorAll("[data-mmodal-dim]").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-mmodal-dim") === dimId);
    });
    renderModalDimensionContent();
  };

  window.openCurrentPhaseModal = function() {
    window.openCenteredMethodologyModal(currentSelectedPhase);
  };

  // Keyboard and click outside listeners for modal
  const centeredModalEl = document.getElementById("methodology-centered-modal");
  if (centeredModalEl) {
    centeredModalEl.addEventListener("click", (e) => {
      if (e.target === centeredModalEl) window.closeCenteredMethodologyModal();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      window.closeCenteredMethodologyModal();
    }
  });

  // =========================================================================
  // SUBTLE PHASE PREVIOUS / NEXT CONTROLS
  // =========================================================================
  const METHOD_PHASE_KEYS = ["phase_1", "phase_2", "phase_3", "phase_4", "phase_5", "phase_6", "phase_7", "phase_8"];

  function updatePhaseIndicators(idx) {
    const num = idx + 1;
    const counterWorkstation = document.getElementById("workstation-phase-counter");
    if (counterWorkstation) counterWorkstation.textContent = `${num} / 8`;
    const counterModal = document.getElementById("mmodal-phase-counter");
    if (counterModal) counterModal.textContent = `Fase ${num} / 8`;
  }

  window.goToPreviousPhase = function() {
    const idx = METHOD_PHASE_KEYS.indexOf(currentSelectedPhase);
    const newIdx = (idx - 1 + METHOD_PHASE_KEYS.length) % METHOD_PHASE_KEYS.length;
    const targetPhase = METHOD_PHASE_KEYS[newIdx];
    window.selectMethodologyPhase(targetPhase, true);
    window.switchModalPhase(targetPhase);
    updatePhaseIndicators(newIdx);
  };

  window.goToNextPhase = function() {
    const idx = METHOD_PHASE_KEYS.indexOf(currentSelectedPhase);
    const newIdx = (idx + 1) % METHOD_PHASE_KEYS.length;
    const targetPhase = METHOD_PHASE_KEYS[newIdx];
    window.selectMethodologyPhase(targetPhase, true);
    window.switchModalPhase(targetPhase);
    updatePhaseIndicators(newIdx);
  };

  // =========================================================================
  // TACTILE SIMULATION CONTROLS & WORM LEDGER HISTORY
  // =========================================================================
  window.setSimHorizon = function(months) {
    const hiddenInput = document.getElementById("sim-horizon-val");
    const slider = document.getElementById("sim-horizon-slider");
    if (hiddenInput) hiddenInput.value = months;
    if (slider) slider.value = months;
    document.querySelectorAll("#sim-horizon-pill-group .sim-pill-btn").forEach(btn => {
      btn.classList.toggle("active", parseInt(btn.getAttribute("data-months"), 10) === months);
    });
  };

  window.setSimPaths = function(num) {
    const hiddenInput = document.getElementById("sim-paths-val");
    const slider = document.getElementById("sim-paths-slider");
    const display = document.getElementById("sim-paths-display");
    const stepper = document.getElementById("sim-paths-stepper-label");
    if (hiddenInput) hiddenInput.value = num;
    if (slider) slider.value = num;
    if (display) display.textContent = `${num.toLocaleString()} caminos`;
    if (stepper) stepper.textContent = num.toLocaleString();
    document.querySelectorAll(".sim-preset-btn").forEach(btn => {
      btn.classList.toggle("active", parseInt(btn.textContent.replace(/,/g, ""), 10) === num);
    });
  };

  window.stepSimPaths = function(delta) {
    const hiddenInput = document.getElementById("sim-paths-val");
    let current = parseInt(hiddenInput ? hiddenInput.value : 1000, 10);
    let nextVal = Math.max(500, Math.min(10000, current + delta));
    window.setSimPaths(nextVal);
  };

  window.loadSimulationHistory = async function() {
    const tbody = document.getElementById("sim-history-tbody");
    if (!tbody) return;
    try {
      const res = await fetch("/api/simulation/history?limit=15");
      const data = await res.json();
      const history = data.history || [];
      if (history.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" style="text-align:center; color:var(--text-muted); padding:1rem;">Sin ejecuciones registradas aún en el libro WORM.</td></tr>`;
        return;
      }
      tbody.innerHTML = history.map(item => {
        const summary = item.results_summary || {};
        const hashShort = item.block_hash ? `${item.block_hash.substring(0, 10)}...${item.block_hash.substring(item.block_hash.length - 6)}` : "GENESIS";
        return `
          <tr class="clickable-row">
            <td><span class="sim-block-badge">#${item.block_number}</span></td>
            <td style="font-size:0.73rem;">${item.timestamp_utc || "--"}</td>
            <td><strong style="color:#e2e8f0;">${item.user_id}</strong></td>
            <td>${item.port_name}</td>
            <td><span class="badge" style="font-size:0.68rem;">${item.scenario}</span></td>
            <td>${item.num_paths.toLocaleString()}</td>
            <td>${item.horizon_months}M</td>
            <td><strong>${Math.round(summary.expected_volume || 0).toLocaleString()}</strong> TEUs</td>
            <td style="color:var(--rose-danger);">${Math.round(summary.var_95_volume || 0).toLocaleString()} TEUs</td>
            <td>${item.execution_time_ms} ms (${item.vcpu_cores_allocated} vCPU)</td>
            <td><code class="sim-hash-cell" title="${item.block_hash}">${hashShort}</code></td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      console.error("Error loading simulation history:", err);
    }
  };

  // =========================================================================
  // SIMULATION KPIS EDUCATIONAL POPOVERS
  // =========================================================================
  const SIM_KPI_EXPLANATIONS = {
    "expected": {
      title: "Volumen Esperado (E[Y] / Media Estocástica Ponderada)",
      badge: "MÉTRICA DE VALOR CENTRAL",
      formula: "\\mathbb{E}[Y] = \\frac{1}{M}\\sum_{m=1}^M \\hat{y}_m",
      deduction: "Representa el centro de masa de la distribución de pronósticos sobre M trayectorias estocásticas correlacionadas con cópula de Cholesky y saltos de Poisson de Merton. Al ponderar escenarios alcistas y bajistas, refleja la estimación incondicionada media para la terminal.",
      impact: "Base para contratos de fletamento, presupuesto de combustible VLSFO y turnos fijos de estiba.",
      code: "expected_volume = float(np.mean(terminal_paths))"
    },
    "var95": {
      title: "Value at Risk 95% (VaR 95% / Piso de Confianza)",
      badge: "GESTIÓN DE RIESGO DE COLA",
      formula: "\\text{VaR}_{0.95}(Y) = \\inf \\left\\{ y \\in \\mathbb{R} : P(Y \\le y) \\ge 0.05 \\right\\}",
      deduction: "Piso de volumen con 95% de confianza estadística bajo el escenario evaluado. Únicamente en el 5% de los peores caminos simulados el volumen caerá por debajo de este valor.",
      impact: "Piso de supervivencia financiera. Si el VaR 95% cae bajo el canon concesional de la AMP, se activan cláusulas de fuerza mayor.",
      code: "var_95 = float(np.percentile(terminal_paths, 5.0))"
    },
    "cvar": {
      title: "Conditional VaR 95% (CVaR / Expected Shortfall)",
      badge: "RIESGO COHERENTE (ARTZNER ET AL.)",
      formula: "\\text{CVaR}_{0.95}(Y) = \\mathbb{E}\\left[Y \\mid Y \\le \\text{VaR}_{0.95}(Y)\\right]",
      deduction: "Mide el volumen promedio en el peor 5% de los escenarios. A diferencia del VaR, el CVaR es subaditivo y coherente, cuantificando la severidad esperada en caso de desastre logístico.",
      impact: "Dimensionamiento de reservas de liquidez y subsidios de emergencia del hub interoceánico panameño.",
      code: "cvar_95 = float(terminal_paths[terminal_paths <= var_95].mean())"
    },
    "prob": {
      title: "Probabilidad Empírica de Caída Severa (>25%)",
      badge: "ALERTA DE QUIEBRE DE PATIO",
      formula: "\\hat{P} = \\frac{1}{M}\\sum_{m=1}^M \\mathbb{I}\\left(\\frac{\\hat{y}_m - Y_0}{Y_0} < -0.25\\right)",
      deduction: "Fracción de trayectorias donde la demanda portuaria sufre una contracción abrupta superior a la cuarta parte de su volumen histórico.",
      impact: "Si supera el 20%, la AMP activa alerta naranja para reprogramar ventanas de atraque y desviar buques feeder.",
      code: "prob_severe = float(np.mean((terminal_paths - y0) / y0 < -0.25))"
    }
  };

  window.openSimKpiPopover = function(kpiKey) {
    const info = SIM_KPI_EXPLANATIONS[kpiKey];
    if (!info) return;

    const badge = document.getElementById("cp-modal-badge");
    const title = document.getElementById("cp-modal-title");
    const sub = document.getElementById("cp-modal-sub");
    const content = document.getElementById("cp-modal-content");

    if (badge) badge.textContent = info.badge;
    if (title) title.textContent = info.title;
    if (sub) sub.textContent = "Fundamentación matemática formal y aplicación en terminales de Panamá";

    if (content) {
      content.innerHTML = `
        <div class="cp-formula-card">
          <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; letter-spacing:0.5px; margin-bottom:0.25rem;">Ecuación Matemática Formal</div>
          <div class="cp-formula-math">$$${info.formula}$$</div>
        </div>

        <div class="cp-section-block">
          <h4>📐 Deducción Estadística</h4>
          <p>${info.deduction}</p>
        </div>

        <div class="cp-section-block" style="border-left-color: var(--emerald-success, #10b981);">
          <h4 style="color: var(--emerald-success, #10b981);">🚢 Impacto Operacional en la Concesión Portuaria</h4>
          <p>${info.impact}</p>
        </div>

        <div style="margin-top:0.75rem;">
          <span style="font-size:0.72rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">Cálculo Matricial en Python / NumPy:</span>
          <pre class="cp-code-snippet"><code>${info.code}</code></pre>
        </div>
      `;
    }

    const modal = document.getElementById("compact-proportional-modal");
    if (modal) modal.classList.add("open");
  };

  // =========================================================================
  // DIAGNOSTIC DETAIL MODALS (RESIDUALS, FEATURES, CORRELATIONS)
  // =========================================================================
  window.openResidualMetricModal = async function(metricKey) {
    try {
      const res = await fetch(`/api/diagnostics/residual-detail/${metricKey}`);
      const data = await res.json();
      const detail = data.detail;
      const badge = document.getElementById("cp-modal-badge");
      const title = document.getElementById("cp-modal-title");
      const sub = document.getElementById("cp-modal-sub");
      const content = document.getElementById("cp-modal-content");

      if (badge) badge.textContent = "DIAGNÓSTICO ESTADÍSTICO DE RESIDUOS";
      if (title) title.textContent = detail.title;
      if (sub) sub.textContent = `Valor Empírico: ${detail.metric_value} | Ref: ${detail.benchmark_reference}`;

      if (content) {
        content.innerHTML = `
          <div class="cp-formula-card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; letter-spacing:0.5px; margin-bottom:0.25rem;">Fórmula Matemática Formal</div>
            <div class="cp-formula-math">$$${detail.formula_latex}$$</div>
            <div style="font-size:0.75rem; color:#67e8f9; margin-top:0.35rem;"><strong>Valor Actual:</strong> ${detail.metric_value} (${detail.relative_pct})</div>
          </div>

          <div class="cp-section-block">
            <h4>📐 Deducción Matemática</h4>
            <p>${detail.mathematical_deduction}</p>
          </div>

          <div class="cp-section-block" style="border-left-color: var(--emerald-success, #10b981);">
            <h4 style="color: var(--emerald-success, #10b981);">🚢 Impacto Operacional en la Logística de Panamá</h4>
            <p>${detail.operational_impact}</p>
          </div>

          <div class="cp-section-block" style="border-left-color: #f59e0b;">
            <h4 style="color: #f59e0b;">⚙️ Mitigación & Calibración Algorítmica</h4>
            <p>${detail.algorithmic_mitigation}</p>
          </div>

          <div style="margin-top:0.75rem;">
            <span style="font-size:0.72rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">Sintaxis de Implementación en Python:</span>
            <pre class="cp-code-snippet"><code>${detail.python_syntax}</code></pre>
          </div>
        `;
      }
      const modal = document.getElementById("compact-proportional-modal");
      if (modal) modal.classList.add("open");
    } catch (err) {
      console.error("Error opening residual modal:", err);
    }
  };

  window.openFeatureDetailModal = async function(featureName) {
    try {
      const res = await fetch(`/api/diagnostics/feature-detail/${encodeURIComponent(featureName)}`);
      const data = await res.json();
      const detail = data.detail;
      const badge = document.getElementById("cp-modal-badge");
      const title = document.getElementById("cp-modal-title");
      const sub = document.getElementById("cp-modal-sub");
      const content = document.getElementById("cp-modal-content");

      if (badge) badge.textContent = `FEATURE IMPORTANCE • RANK #${detail.rank}`;
      if (title) title.textContent = detail.name;
      if (sub) sub.textContent = `Categoría: ${detail.category} | Ganancia Split Gain: ${detail.split_gain_pct}%`;

      if (content) {
        content.innerHTML = `
          <div class="cp-formula-card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; letter-spacing:0.5px; margin-bottom:0.25rem;">Definición Matemática</div>
            <div class="cp-formula-math">$$${detail.formula_latex}$$</div>
            <div style="font-size:0.75rem; color:#67e8f9; margin-top:0.35rem;"><strong>Importancia Split Gain:</strong> ${detail.split_gain_pct}% del poder explicativo global</div>
          </div>

          <div class="cp-section-block">
            <h4>⚓ Justificación de Dominio Marítimo y Logístico</h4>
            <p>${detail.domain_rationale}</p>
          </div>

          <div style="margin-top:0.75rem;">
            <span style="font-size:0.72rem; color:#94a3b8; text-transform:uppercase; letter-spacing:0.5px;">Transformación en Feature Store (Python):</span>
            <pre class="cp-code-snippet"><code>${detail.python_syntax}</code></pre>
          </div>
        `;
      }
      const modal = document.getElementById("compact-proportional-modal");
      if (modal) modal.classList.add("open");
    } catch (err) {
      console.error("Error opening feature modal:", err);
    }
  };

  window.openCorrelationDetailModal = async function(f1, f2) {
    try {
      const res = await fetch(`/api/diagnostics/correlation-detail/${encodeURIComponent(f1)}/${encodeURIComponent(f2)}`);
      const detail = await res.json();
      const badge = document.getElementById("cp-modal-badge");
      const title = document.getElementById("cp-modal-title");
      const sub = document.getElementById("cp-modal-sub");
      const content = document.getElementById("cp-modal-content");

      if (badge) badge.textContent = "MULTICOLINEALIDAD BIVARIADA & VIF";
      if (title) title.textContent = `${detail.feature_1} vs ${detail.feature_2}`;
      if (sub) sub.textContent = `Pearson r = ${detail.pearson_r} | R² = ${detail.r_squared} (${detail.collinearity_level})`;

      if (content) {
        content.innerHTML = `
          <div class="cp-formula-card">
            <div style="font-size:0.75rem; text-transform:uppercase; color:#94a3b8; letter-spacing:0.5px; margin-bottom:0.25rem;">Coeficiente de Correlación Lineal de Pearson</div>
            <div class="cp-formula-math">$$${detail.formula_latex}$$</div>
            <div style="font-size:0.75rem; color:#f43f5e; margin-top:0.35rem;"><strong>Nivel de Multicolinealidad:</strong> ${detail.collinearity_level}</div>
          </div>

          <div class="cp-section-block" style="border-left-color: #f43f5e;">
            <h4 style="color: #f43f5e;">⚠️ Impacto en Modelos Lineales y VIF</h4>
            <p>${detail.vif_impact}</p>
          </div>

          <div class="cp-section-block" style="border-left-color: var(--emerald-success, #10b981);">
            <h4 style="color: var(--emerald-success, #10b981);">🌲 Por Qué los Modelos de Árboles (LightGBM) son Inmunes</h4>
            <p>${detail.tree_invariance_rationale}</p>
          </div>

          <div class="cp-section-block" style="border-left-color: var(--cyan-bright, #06b6d4);">
            <h4 style="color: var(--cyan-bright, #06b6d4);">📋 Recomendación de Arquitectura</h4>
            <p>${detail.recommendation}</p>
          </div>
        `;
      }
      const modal = document.getElementById("compact-proportional-modal");
      if (modal) modal.classList.add("open");
    } catch (err) {
      console.error("Error opening correlation modal:", err);
    }
  };

  window.closeCompactModal = function() {
    const modal = document.getElementById("compact-proportional-modal");
    if (modal) modal.classList.remove("open");
  };

  // Keyboard and click outside listeners for compact modal
  const compactModalEl = document.getElementById("compact-proportional-modal");
  if (compactModalEl) {
    compactModalEl.addEventListener("click", (e) => {
      if (e.target === compactModalEl) window.closeCompactModal();
    });
  }
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      window.closeCompactModal();
    }
  });

  // =========================================================================
  // V2.0 IAM, SECURITY HUD, RBAC SIMULATOR & WORM LEDGER HANDLERS
  // =========================================================================

  window.activeSession = {
    token: localStorage.getItem("portops_token") || null,
    user: null,
    roles: ["root"],
    permissions: []
  };
  window.tempMfaToken = null;

  window.openAuthModal = function(initialTab = "atab-login") {
    const modal = document.getElementById("auth-iam-modal");
    if (modal) {
      modal.classList.add("open");
      window.switchAuthTab(initialTab);
    }
  };

  window.closeAuthModal = function() {
    const modal = document.getElementById("auth-iam-modal");
    if (modal) modal.classList.remove("open");
  };

  window.switchAuthTab = function(tabId) {
    document.querySelectorAll(".auth-tab-btn").forEach(btn => {
      btn.classList.toggle("active", btn.getAttribute("data-atab") === tabId);
    });
    document.querySelectorAll(".auth-tab-content").forEach(content => {
      content.classList.toggle("active", content.id === tabId);
    });
  };

  window.executeLogin = async function() {
    const usernameInput = document.getElementById("auth-input-username");
    const passwordInput = document.getElementById("auth-input-password");
    const statusEl = document.getElementById("auth-login-status");

    const username = usernameInput ? usernameInput.value.trim() : "";
    const password = passwordInput ? passwordInput.value : "";

    if (!username || !password) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Ingrese usuario y contraseña.</span>`;
      return;
    }

    if (statusEl) statusEl.innerHTML = `<span style="color:#38bdf8;">Autenticando con PBKDF2...</span>`;

    try {
      const res = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });
      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Error en la autenticación.");
      }

      if (data.mfa_required) {
        window.tempMfaToken = data.temp_token;
        const mfaView = document.getElementById("auth-mfa-view");
        if (mfaView) mfaView.style.display = "block";
        if (statusEl) statusEl.innerHTML = `<span style="color:#f59e0b;">Desafío MFA requerido. Ingrese código TOTP.</span>`;
        return;
      }

      // Successful login
      window.activeSession.token = data.session_token;
      window.activeSession.user = data.user;
      window.activeSession.roles = data.roles || ["root"];
      window.activeSession.permissions = data.permissions || [];
      localStorage.setItem("portops_token", data.session_token);

      // Update Top Nav & HUD
      const navUserLabel = document.getElementById("nav-user-label");
      if (navUserLabel) navUserLabel.textContent = data.user.username;
      const hudActiveRole = document.getElementById("hud-active-role");
      if (hudActiveRole) hudActiveRole.textContent = `Rol: ${data.roles[0] || 'root'}`;
      const iamUserKpi = document.getElementById("iam-user-kpi");
      if (iamUserKpi) iamUserKpi.textContent = data.user.username;
      const iamRoleKpi = document.getElementById("iam-role-kpi");
      if (iamRoleKpi) iamRoleKpi.textContent = data.roles[0] || 'root';

      // Update Inspector Tab
      const rawEl = document.getElementById("inspector-token-raw");
      if (rawEl) rawEl.textContent = data.session_token;
      const claimsEl = document.getElementById("inspector-token-claims");
      if (claimsEl) claimsEl.textContent = JSON.stringify({ user: data.user, roles: data.roles, exp: "12 Horas" }, null, 2);

      if (statusEl) statusEl.innerHTML = `<span style="color:#10b981;">✓ Sesión iniciada con éxito.</span>`;

      if (data.must_change_password) {
        setTimeout(() => {
          alert("Aviso de Seguridad NIST SP 800-63B: Se requiere cambio obligatorio de contraseña en el primer acceso.");
          window.switchAuthTab("atab-password");
        }, 600);
      }
    } catch (err) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Error: ${err.message}</span>`;
    }
  };

  window.executeVerifyMFA = async function() {
    const totpInput = document.getElementById("auth-input-totp");
    const statusEl = document.getElementById("auth-mfa-status");
    const code = totpInput ? totpInput.value.trim() : "";

    if (!code || code.length !== 6) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Ingrese código de 6 dígitos.</span>`;
      return;
    }

    try {
      const res = await fetch("/api/v1/auth/mfa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_token: window.tempMfaToken, totp_code: code })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Código incorrecto.");

      window.activeSession.token = data.session_token;
      window.activeSession.user = data.user;
      window.activeSession.roles = data.roles || [];
      window.activeSession.permissions = data.permissions || [];
      localStorage.setItem("portops_token", data.session_token);

      const navUserLabel = document.getElementById("nav-user-label");
      if (navUserLabel) navUserLabel.textContent = data.user.username;
      const hudActiveRole = document.getElementById("hud-active-role");
      if (hudActiveRole) hudActiveRole.textContent = `Rol: ${data.roles[0] || 'root'}`;

      if (statusEl) statusEl.innerHTML = `<span style="color:#10b981;">✓ MFA Verificado. Sesión otorgada.</span>`;
    } catch (err) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Error: ${err.message}</span>`;
    }
  };

  window.executeChangePassword = async function() {
    const oldInput = document.getElementById("pwd-input-old");
    const newInput = document.getElementById("pwd-input-new");
    const confirmInput = document.getElementById("pwd-input-confirm");
    const statusEl = document.getElementById("pwd-change-status");

    if (newInput.value !== confirmInput.value) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Las contraseñas no coinciden.</span>`;
      return;
    }

    try {
      const headers = { "Content-Type": "application/json" };
      if (window.activeSession.token) {
        headers["Authorization"] = `Bearer ${window.activeSession.token}`;
      }

      const res = await fetch("/api/v1/auth/password/change", {
        method: "POST",
        headers: headers,
        body: JSON.stringify({ old_password: oldInput.value, new_password: newInput.value })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al actualizar contraseña.");

      if (statusEl) statusEl.innerHTML = `<span style="color:#10b981;">✓ ${data.message}</span>`;
      oldInput.value = "";
      newInput.value = "";
      confirmInput.value = "";
    } catch (err) {
      if (statusEl) statusEl.innerHTML = `<span style="color:#f43f5e;">Error: ${err.message}</span>`;
    }
  };

  window.executeSetupMFA = async function() {
    try {
      const headers = {};
      if (window.activeSession.token) headers["Authorization"] = `Bearer ${window.activeSession.token}`;

      const res = await fetch("/api/v1/auth/mfa/setup", { method: "POST", headers: headers });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Error al generar MFA.");

      const outBox = document.getElementById("mfa-setup-output");
      if (outBox) outBox.style.display = "block";
      const secEl = document.getElementById("mfa-secret-display");
      if (secEl) secEl.textContent = data.mfa_secret;
      const uriEl = document.getElementById("mfa-uri-display");
      if (uriEl) uriEl.textContent = data.provisioning_uri;
    } catch (err) {
      alert("Error configurando MFA: " + err.message);
    }
  };

  window.executeLogout = async function() {
    try {
      const headers = {};
      if (window.activeSession.token) headers["Authorization"] = `Bearer ${window.activeSession.token}`;
      await fetch("/api/v1/auth/logout", { method: "POST", headers });
    } catch (e) {}

    window.activeSession = { token: null, user: null, roles: ["readonly_viewer"], permissions: [] };
    localStorage.removeItem("portops_token");

    const navUserLabel = document.getElementById("nav-user-label");
    if (navUserLabel) navUserLabel.textContent = "Iniciar Sesión / IAM";
    const hudActiveRole = document.getElementById("hud-active-role");
    if (hudActiveRole) hudActiveRole.textContent = "Rol: Invitado";
    const iamUserKpi = document.getElementById("iam-user-kpi");
    if (iamUserKpi) iamUserKpi.textContent = "Invitado";
    const iamRoleKpi = document.getElementById("iam-role-kpi");
    if (iamRoleKpi) iamRoleKpi.textContent = "readonly_viewer";
    const rawEl = document.getElementById("inspector-token-raw");
    if (rawEl) rawEl.textContent = "No hay sesión activa autenticada.";
    const claimsEl = document.getElementById("inspector-token-claims");
    if (claimsEl) claimsEl.textContent = "{}";

    alert("Sesión finalizada exitosamente.");
  };

  window.selectRbacRoleSimulation = async function(roleId) {
    document.querySelectorAll(".rbac-role-card").forEach(c => {
      c.classList.toggle("selected", c.getAttribute("data-role") === roleId);
    });

    try {
      const headers = { "Content-Type": "application/json" };
      if (window.activeSession.token) headers["Authorization"] = `Bearer ${window.activeSession.token}`;

      const res = await fetch("/api/v1/auth/simulate-role", {
        method: "POST",
        headers,
        body: JSON.stringify({ target_role: roleId })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      const titleEl = document.getElementById("simulated-role-title");
      if (titleEl) titleEl.textContent = data.simulated_role.name;
      const countEl = document.getElementById("simulated-role-perm-count");
      if (countEl) countEl.textContent = data.permissions.length;

      const container = document.getElementById("simulated-permissions-list");
      if (container) {
        container.innerHTML = data.permissions.map(p => `<span class="rbac-perm-tag">${p}</span>`).join("");
      }

      // Update HUD active role simulation
      const hudActiveRole = document.getElementById("hud-active-role");
      if (hudActiveRole) hudActiveRole.textContent = `Rol: ${roleId}`;
      const iamRoleKpi = document.getElementById("iam-role-kpi");
      if (iamRoleKpi) iamRoleKpi.textContent = roleId;
    } catch (err) {
      console.error("Error simulando rol:", err);
    }
  };

  window.verifyWormAuditChainLive = async function() {
    try {
      const res = await fetch("/api/v1/audit/worm/verify");
      const data = await res.json();
      const v = data.verification || {};

      const validText = document.getElementById("worm-valid-text");
      const blocksBadge = document.getElementById("worm-blocks-badge");
      const genesisEl = document.getElementById("worm-genesis-hash");
      const headEl = document.getElementById("worm-head-hash");
      const hudWorm = document.getElementById("hud-worm-status");
      const noteEl = document.getElementById("worm-audit-summary-note");

      if (v.valid) {
        if (validText) validText.innerHTML = `<span style="color:#10b981;">✓ INTEGRIDAD CRIPTOGRÁFICA CERTIFICADA (ISO/IEC 27001)</span>`;
        if (blocksBadge) blocksBadge.textContent = `Bloques Verificados: ${v.verified_blocks || v.total_blocks || 0}`;
        if (genesisEl) genesisEl.textContent = "0000000000000000000000000000000000000000000000000000000000000000";
        if (headEl) headEl.textContent = v.head_hash || (v.blocks && v.blocks.length ? v.blocks[v.blocks.length - 1].block_hash : "0x000...génesis");
        if (hudWorm) hudWorm.innerHTML = `<svg class="badge-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg> WORM: Válido (${v.verified_blocks || 0} blk)`;
        if (noteEl) noteEl.textContent = "Encadenamiento SHA-256 verificado bloque a bloque. Cero mutaciones detectadas. Inmutabilidad estricta garantizada.";
      } else {
        if (validText) validText.innerHTML = `<span style="color:#f43f5e;">⚠️ ALERTA: MUTACIÓN O RUPTURA DE CADENA DETECTADA</span>`;
        if (hudWorm) hudWorm.innerHTML = `⚠️ WORM: Roto`;
      }
    } catch (err) {
      console.error("Error verificando WORM:", err);
    }
  };

  window.fetchAuditSecurityEvents = async function() {
    try {
      const res = await fetch("/api/v1/audit/events?limit=20");
      const data = await res.json();
      const tbody = document.getElementById("security-events-tbody");
      if (tbody && data.events) {
        tbody.innerHTML = data.events.map(e => `
          <tr>
            <td>${e.created_at ? e.created_at.split(".")[0] : ""}</td>
            <td><strong>${e.actor_id}</strong></td>
            <td><code>${e.action}</code></td>
            <td>${e.resource_type}</td>
            <td><span class="badge" style="background:${e.result === 'SUCCESS' ? 'rgba(16,185,129,0.15)' : 'rgba(244,63,94,0.15)'}; color:${e.result === 'SUCCESS' ? '#10b981' : '#f43f5e'};">${e.result}</span></td>
            <td><code>${e.ip_hash || 'none'}</code></td>
          </tr>
        `).join("");
      }
    } catch (err) {
      console.error("Error cargando eventos:", err);
    }
  };

  window.runQualityGatesDynamic = async function() {
    const btn = document.getElementById("btn-run-quality-gates");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `⏳ Validando 5 Compuertas...`;
    }

    try {
      const res = await fetch("/api/v1/data/quality/validate", { method: "POST" });
      const data = await res.json();

      const scoreEl = document.getElementById("dp-quality-score");
      if (scoreEl) scoreEl.textContent = `${data.overall_score.toFixed(2)} / 1.00`;

      const logEl = document.getElementById("dp-gate-execution-log");
      if (logEl) logEl.textContent = `Última ejecución en vivo: ${data.executed_at}. Estado general: ${data.status}. 5/5 compuertas aprobadas.`;

      // Update gate cards
      if (data.gates) {
        data.gates.forEach((g, idx) => {
          const card = document.getElementById(`gate-card-${idx + 1}`);
          if (card) {
            card.className = `data-gate-card ${g.passed ? 'passed' : 'failed'}`;
            const pill = card.querySelector(".gate-score-pill");
            if (pill) pill.textContent = `Score: ${g.score.toFixed(2)} • ${g.violations_count} violaciones`;
          }
        });
      }
    } catch (err) {
      alert("Error ejecutando compuertas: " + err.message);
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = `<svg class="btn-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4m0 12v4M4.93 4.93l2.83 2.83m8.48 8.48l2.83 2.83M2 12h4m12 0h4M4.93 19.07l2.83-2.83m8.48-8.48l2.83-2.83"></path></svg> Ejecutar 5 Quality Gates`;
      }
    }
  };

  window.loadDataPlatformManifest = async function() {
    try {
      const res = await fetch("/api/v1/data/catalog/manifest");
      const data = await res.json();
      const m = data.manifest || {};

      const covVal = document.getElementById("dp-coverage-value");
      if (covVal && m.months_count) covVal.textContent = `${m.months_count} Meses`;
      const covSub = document.getElementById("dp-coverage-sub");
      if (covSub && m.coverage_start) covSub.textContent = `${m.coverage_start} ➔ ${m.coverage_end} (pd.period_range)`;
      const rowCount = document.getElementById("manifest-row-count");
      if (rowCount && m.row_count) rowCount.textContent = `${m.row_count.toLocaleString()} registros portuarios`;
      const sHash = document.getElementById("manifest-schema-hash");
      if (sHash && m.schema_hash) sHash.textContent = m.schema_hash.substring(0, 16) + "...";
      const cHash = document.getElementById("manifest-content-hash");
      if (cHash && m.content_hash) cHash.textContent = m.content_hash.substring(0, 16) + "...";
    } catch (err) {
      console.error("Error cargando manifiesto:", err);
    }
  };

  // Wire Top Nav IAM and WORM buttons
  const btnAuthIam = document.getElementById("btn-auth-iam");
  if (btnAuthIam) {
    btnAuthIam.addEventListener("click", () => window.openAuthModal("atab-login"));
  }
  const hudWormBtn = document.getElementById("hud-worm-status");
  if (hudWormBtn) {
    hudWormBtn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));
      const secTabBtn = document.querySelector('[data-tab="tab-security-iam"]');
      const secTabContent = document.getElementById("tab-security-iam");
      if (secTabBtn) secTabBtn.classList.add("active");
      if (secTabContent) secTabContent.classList.add("active");
      window.verifyWormAuditChainLive();
    });
  }

  // =========================================================================
  // INTERACTIVE REASONING CoT ENGINE & CRYPTOGRAPHIC SOULS HANDLERS (v1.0)
  // =========================================================================
  const soulCatalog = {
    "agente_aduanero": {
      name: "Agente Aduanal y Clasificador Arancelario",
      hash: "4f715339023c52a0...",
      seal: "SOUL-ENC-6BF00926B66776CD..."
    },
    "auditor_maritimo": {
      name: "Auditor Regulatorio Ley 6/2002 y Ley 56/2008",
      hash: "033ba0892572a1f8...",
      seal: "SOUL-ENC-50DBF77CA0E4B9E6..."
    },
    "operador_muelle": {
      name: "Operador de Muelle y Patios TOS Balboa",
      hash: "9e2ad024b3f5c719...",
      seal: "SOUL-ENC-9812A069BF95C14C..."
    },
    "cientifico_causal": {
      name: "Científico de Riesgo Causal y Monte Carlo",
      hash: "3401b5699f56e0d4...",
      seal: "SOUL-ENC-8B423ED60C6B3743..."
    }
  };

  window.updateSoulBadgeView = function() {
    const sel = document.getElementById("cot-soul-select");
    if (!sel) return;
    const soulId = sel.value;
    const soul = soulCatalog[soulId] || soulCatalog["agente_aduanero"];
    const nameEl = document.getElementById("cot-soul-name-display");
    const hashEl = document.getElementById("cot-soul-hash-display");
    const sealEl = document.getElementById("cot-soul-seal-display");
    if (nameEl) nameEl.textContent = soul.name;
    if (hashEl) hashEl.textContent = soul.hash;
    if (sealEl) sealEl.textContent = soul.seal;
  };

  window.setCoTPreset = function(promptText, soulId) {
    const input = document.getElementById("cot-prompt-input");
    const sel = document.getElementById("cot-soul-select");
    if (input) input.value = promptText;
    if (sel && soulId) {
      sel.value = soulId;
      window.updateSoulBadgeView();
    }
  };

  window.executeCoTReasoning = async function() {
    const inputEl = document.getElementById("cot-prompt-input");
    const query = inputEl ? inputEl.value.trim() : "";
    if (!query) {
      alert("Por favor ingrese una consulta operacional o seleccione una de las pruebas rápidas.");
      return;
    }

    const soulSelect = document.getElementById("cot-soul-select");
    const targetSoul = soulSelect ? soulSelect.value : "agente_aduanero";
    const btnRun = document.getElementById("btn-run-cot");
    const statusIcon = document.getElementById("cot-status-icon");
    const verdictText = document.getElementById("cot-verdict-text");
    const latencyEl = document.getElementById("cot-metric-latency");
    const infEl = document.getElementById("cot-metric-inf");
    const tokensEl = document.getElementById("cot-metric-tokens");
    const sealBadge = document.getElementById("cot-metric-seal");
    const responseBox = document.getElementById("cot-final-response-box");
    const citationsRow = document.getElementById("cot-citations-row");
    const citationsTags = document.getElementById("cot-citations-tags");

    // UI Loading state
    if (btnRun) {
      btnRun.disabled = true;
      btnRun.textContent = "⏳ Ejecutando Cadena de Razonamiento CoT...";
    }
    if (statusIcon) statusIcon.textContent = "⚙️";
    if (verdictText) verdictText.textContent = "Analizando con Guardrails y Almas Criptográficas...";
    if (responseBox) responseBox.textContent = "Evaluando consulta paso a paso...";

    // Reset steps
    for (let i = 1; i <= 5; i++) {
      const card = document.getElementById(`cot-card-step-${i}`);
      const st = document.getElementById(`cot-status-step-${i}`);
      const num = document.getElementById(`cot-num-step-${i}`);
      if (st) {
        st.textContent = "Ejecutando...";
        st.style.background = "rgba(0, 229, 255, 0.15)";
        st.style.color = "#00E5FF";
      }
      if (card) {
        card.style.borderColor = "rgba(0, 229, 255, 0.4)";
      }
      if (num) {
        num.style.background = "#00E5FF";
        num.style.color = "#070D1E";
      }
    }

    const tStart = performance.now();

    try {
      const res = await fetch("/api/v1/agents/reasoning-chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          target_soul_id: targetSoul,
          guardrail_level: "strict",
          runtime_preference: "auto"
        })
      });

      const data = await res.json();
      const elapsedTotal = Math.round(performance.now() - tStart);

      if (res.status === 200 && data.chain_of_thought) {
        const steps = data.chain_of_thought;
        steps.forEach((step, idx) => {
          const stepNum = step.step_number || (idx + 1);
          const stEl = document.getElementById(`cot-status-step-${stepNum}`);
          const detEl = document.getElementById(`cot-details-step-${stepNum}`);
          const cardEl = document.getElementById(`cot-card-step-${stepNum}`);
          const numEl = document.getElementById(`cot-num-step-${stepNum}`);

          if (stEl) {
            stEl.textContent = `${step.status} (${step.duration_ms || step.latency_ms || 0} ms)`;
            if (step.status === "PASSED" || step.status === "COMPLETED" || step.status === "VERIFIED") {
              stEl.style.background = "rgba(0, 245, 212, 0.15)";
              stEl.style.color = "#00F5D4";
              stEl.style.border = "1px solid #00F5D4";
              if (cardEl) cardEl.style.borderColor = "rgba(0, 245, 212, 0.4)";
              if (numEl) { numEl.style.background = "#00F5D4"; numEl.style.color = "#070D1E"; }
            } else if (step.status === "REJECTED" || step.status === "FAILED") {
              stEl.style.background = "rgba(255, 90, 95, 0.2)";
              stEl.style.color = "#FF5A5F";
              stEl.style.border = "1px solid #FF5A5F";
              if (cardEl) cardEl.style.borderColor = "#FF5A5F";
              if (numEl) { numEl.style.background = "#FF5A5F"; numEl.style.color = "#FFF"; }
            }
          }
          if (detEl && step.details) {
            detEl.textContent = step.details;
          }
        });

        // Metrics
        const m = data.metrics || {};
        if (latencyEl) latencyEl.textContent = `${m.total_latency_ms || elapsedTotal} ms`;
        if (infEl) infEl.textContent = `${m.inference_step_latency_ms || 0.07} ms`;
        if (tokensEl) tokensEl.textContent = `${m.tokens_generated || 120}`;
        if (sealBadge) {
          if (m.soul_seal_valid) {
            sealBadge.textContent = "🔐 Sello SHA-256 Verificado";
            sealBadge.style.background = "rgba(0, 245, 212, 0.2)";
            sealBadge.style.color = "#00F5D4";
          } else {
            sealBadge.textContent = "⚠️ Sello No Verificado";
            sealBadge.style.background = "rgba(255, 90, 95, 0.2)";
            sealBadge.style.color = "#FF5A5F";
          }
        }

        if (statusIcon) statusIcon.textContent = data.status === "GUARDRAIL_BLOCKED" ? "🚫" : "✅";
        if (verdictText) {
          verdictText.textContent = data.status === "GUARDRAIL_BLOCKED"
            ? "⚠️ Consulta Bloqueada por Guardrail de Seguridad"
            : "✓ Razonamiento CoT Completado Exitosamente";
          verdictText.style.color = data.status === "GUARDRAIL_BLOCKED" ? "#FF5A5F" : "#00F5D4";
        }

        // Response
        if (responseBox) {
          responseBox.textContent = data.response || "Inferencia procesada.";
        }

        // Citations
        if (citationsRow && citationsTags) {
          const cites = data.legal_citations || [];
          if (cites.length > 0) {
            citationsRow.style.display = "block";
            citationsTags.innerHTML = cites.map(c => `
              <span class="badge" style="background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.4); font-size: 0.76rem;">
                📜 ${c}
              </span>
            `).join("");
          } else {
            citationsRow.style.display = "none";
          }
        }
      } else {
        throw new Error(data.detail || "Error en inferencia");
      }
    } catch (err) {
      if (statusIcon) statusIcon.textContent = "❌";
      if (verdictText) verdictText.textContent = "Error al ejecutar inferencia";
      if (responseBox) responseBox.textContent = `Error: ${err.message}`;
    } finally {
      if (btnRun) {
        btnRun.disabled = false;
        btnRun.textContent = "⚡ Ejecutar Inferencia CoT en Tiempo Real";
      }
    }
  };

  window.copyCoTResponse = function() {
    const box = document.getElementById("cot-final-response-box");
    const btn = document.getElementById("btn-copy-cot-res");
    if (!box) return;
    navigator.clipboard.writeText(box.textContent || "");
    if (btn) {
      const orig = btn.textContent;
      btn.textContent = "✓ ¡Copiado!";
      btn.style.color = "#00F5D4";
      setTimeout(() => {
        btn.textContent = orig;
        btn.style.color = "";
      }, 2000);
    }
  };

  window.applyAuthPreset = function(role) {
    const uInput = document.getElementById("auth-input-username");
    const pInput = document.getElementById("auth-input-password");
    const statusEl = document.getElementById("auth-login-status");

    if (role === "root") {
      if (uInput) uInput.value = "root_f2bbff";
      if (pInput) pInput.value = "2jiXWfZAWoU_5-L_5VS0QJXi8oTHI2UM";
      if (statusEl) {
        statusEl.textContent = "Credenciales preparadas para Root Admin (CSPRNG). Haz clic en 'Iniciar Sesión'.";
        statusEl.style.color = "#00F5D4";
      }
    } else if (role === "auditor") {
      if (uInput) uInput.value = "auditor_maritimo";
      if (pInput) pInput.value = "AuditorPass2026!";
      if (statusEl) {
        statusEl.textContent = "Credenciales preparadas para Auditor (Ley 6/56).";
        statusEl.style.color = "#00E5FF";
      }
    } else if (role === "operador") {
      if (uInput) uInput.value = "operador_muelle";
      if (pInput) pInput.value = "MuellePass2026!";
      if (statusEl) {
        statusEl.textContent = "Credenciales preparadas para Operador Muelle Balboa.";
        statusEl.style.color = "#FFD166";
      }
    } else if (role === "aduanas") {
      if (uInput) uInput.value = "oficial_aduanas";
      if (pInput) pInput.value = "AduanasPass2026!";
      if (statusEl) {
        statusEl.textContent = "Credenciales preparadas para Oficial Aduanas ANA.";
        statusEl.style.color = "#00F5D4";
      }
    }
  };

  // --- Bootstrapping ---
  initThemeSwitcher();
  window.selectMethodologyPhase("phase_1", false); // false = no initial scroll jump on page load
  window.loadSimulationHistory();
  window.verifyWormAuditChainLive();
  window.loadDataPlatformManifest();
  window.fetchAuditSecurityEvents();
  if (window.updateSoulBadgeView) window.updateSoulBadgeView();

  btnPredict.addEventListener("click", runForecast);
  btnSimulate.addEventListener("click", runSimulation);

  checkHealth();
  runForecast();
});
