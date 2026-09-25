# Reporte Ejecutivo de Simulación Monte Carlo y Pruebas de Estrés: Puerto Balboa

## 1. Fundamentos Teóricos y Marco de Gobernanza de Riesgo MLOps
La validación de modelos de Machine Learning no concluye con métricas de test set histórico (WAPE, RMSE).
En logística portuaria y de comercio global, los choques estructurales (*Black Swan events*) alteran la dinámica
operacional. Para cuantificar la solvencia y resiliencia del modelo de pronóstico de la **Autoridad Marítima de Panamá**,
se ejecutó una simulación estocástica de **Monte Carlo** basada en:
- **Perturbaciones Correlacionadas (Cholesky Factorization)**: Preservan las covarianzas entre ratios de transbordo, contenedores vacíos y volumen.
- **Difusión con Saltos de Merton (1976)**: Modela interrupciones abruptas mediante procesos de Poisson ($N_t \sim \text{Poisson}(\lambda \Delta t)$).
- **Métricas de Riesgo Financiero y Logístico**: Value at Risk (**VaR 95%**, **VaR 99%**) y Conditional Value at Risk (**CVaR / Expected Shortfall**).

## 2. Resultados de las Pruebas de Estrés por Escenario (Horizonte: 6 meses)

| Escenario | Volumen Esperado (TEU) | Desv. Est. (TEU) | VaR 95% (Piso) | CVaR 95% (Cola Crítica) | Prob. Caída > 25% | Impacto vs Base |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Baseline** | 198,291 | 12,053 | 176,335 | 172,845 | 0.0% | +0.0% |
| **Canal Drought** | 111,943 | 37,173 | 65,901 | 58,145 | 38.0% | -43.5% |
| **Empty Imbalance** | 188,756 | 19,173 | 159,901 | 150,016 | 1.0% | -4.8% |
| **Bunker Crisis** | 151,401 | 40,942 | 82,915 | 79,257 | 22.0% | -23.6% |
| **Black Swan Compound** | 77,133 | 37,237 | 24,586 | 20,681 | 26.0% | -61.1% |

### Análisis de Métricas de Cola:
- **Value at Risk (VaR 95%)**: Nivel de volumen que garantiza un 95% de confianza de no ser perforado a la baja.
- **Expected Shortfall (CVaR 95%)**: Promedio del volumen en el 5% de las peores trayectorias simuladas. A diferencia del VaR, el CVaR es una **medida coherente de riesgo** (satisface sub-aditividad), crucial para la asignación de reservas de patio de maniobra.
- **Canal Drought**: La caída del 35% en transbordo combinada con saltos de Poisson eleva la probabilidad de caída severa a niveles críticos.
- **Black Swan Compound**: El choque simultáneo de caída de transbordo (-45%) y alza de vacíos (+50%) provoca una contracción extrema en el P10.

## 3. Pruebas de Estrés Inversas (Reverse Stress Testing - RST)
El Reverse Stress Testing no pregunta *'¿qué pasa si ocurre este escenario?'*, sino *'¿cuál es la mínima combinación de fallas operacionales que provoca el colapso del sistema portuario?'*
- **Umbral de Falla Crítica Definido**: Caída de volumen $\ge 25\%$ respecto al baseline.

### Puntos de Inflexión Críticos Detectados (Tipping Points):
| Caída Transbordo (%) | Alza Vacíos (%) | Volumen Proyectado (TEU) | Caída Estimada (%) | ¿Brecha Crítica? |
| :---: | :---: | :---: | :---: | :---: |
| -60.0% | +15.0% | 151,924 | -25.9% | **SÍ** |

## 4. Recomendaciones Operacionales para la Autoridad Marítima de Panamá (AMP)
1. **Monitoreo de Umbral de Vacíos**: Mantener el `empty_ratio` por debajo del 45% en terminales del Pacífico (Balboa/PSA) para evitar estrangulamiento logístico.
2. **Activación de Buffer de Capacidad**: Establecer la capacidad operativa de contingencia alineada con el **CVaR 95%** en lugar del P50 mediano.
3. **Gobernanza de Re-entrenamiento**: Si el drift monitor (`Evidently`) detecta desviaciones multivariadas hacia la frontera del Reverse Stress Test, disparar el pipeline de re-entrenamiento continuo (`make train-champion`).

*(Reporte generado automáticamente por `src/simulation/stress_tester.py`)*
