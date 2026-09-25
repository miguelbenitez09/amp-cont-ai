# Reporte de Comportamiento Estadístico y Ajuste de Distribuciones

## 1. Contexto Metodológico y MLOps Foundations
Para someter a prueba de estrés un modelo en producción (especialmente modelos supervisados como LightGBM),
es imperativo caracterizar no solo la media y varianza de los features de entrada, sino su **morfología estocástica completa**:
- **Asimetría (Skewness)** y **Curtosis (Kurtosis)** para detectar colas pesadas (*Fat Tails*).
- **Ajuste de Bondad de Ajuste (Goodness-of-Fit)** mediante el estadístico de Kolmogorov-Smirnov ($D_{KS}$ y $p$-valor).
- **Estructura de Covarianza Multivariada** para simular perturbaciones correlacionadas mediante descomposición de Cholesky ($L L^T = \Sigma$).

## 2. Resumen Descriptivo y Mejor Distribución Paramétrica por Variable

| Variable | Media | Desv. Est. | Mediana | Asimetría | Curtosis | Mejor Distribución | KS Stat | KS p-valor |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `teu_total` | 111,713.98 | 78,976.95 | 99,230.50 | 0.28 | -1.00 | **t** | 0.0908 | 0.0000 |
| `transshipment_ratio` | 0.58 | 0.42 | 0.85 | -0.58 | -1.54 | **t** | 0.2793 | 0.0000 |
| `empty_ratio` | 0.40 | 0.26 | 0.38 | 2.60 | 19.50 | **t** | 0.0475 | 0.0439 |
| `local_ratio` | 0.17 | 0.27 | 0.09 | 2.26 | 3.88 | **t** | 0.1895 | 0.0000 |
| `teu_unit_factor` | 1.82 | 0.16 | 1.78 | 0.98 | 0.51 | **t** | 0.1643 | 0.0000 |
| `teu_total_lag_1` | 111,448.59 | 78,868.72 | 99,027.00 | 0.28 | -1.00 | **t** | 0.0907 | 0.0000 |

### Interpretación de Formas de Distribución:
- **`teu_total`**: Se ajusta predominantemente a distribuciones asimétricas positivas (`lognorm` / `gamma`), lo que refleja que el tráfico portuario tiene un piso natural en cero y picos asociados a temporadas altas.
- **`transshipment_ratio` y `empty_ratio`**: Definidos estrictamente en el dominio $[0, 1]$. La distribución `beta` provee la aproximación más fiel al capturar la concentración modal del transbordo panameño (entre 80% y 95%).
- **`teu_unit_factor`**: Rango estrecho centrado en ~1.60 TEUs por contenedor, compatible con modelos Gaussianos y Student-$t$.

## 3. Matriz de Correlación Empírica entre Variables Conductoras

| Variable | `teu_total` | `transshipment_ratio` | `empty_ratio` | `local_ratio` | `teu_unit_factor` | `teu_total_lag_1` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `teu_total` | 1.000 | 0.362 | -0.108 | -0.433 | -0.266 | 0.984 |
| `transshipment_ratio` | 0.362 | 1.000 | -0.004 | -0.345 | -0.055 | 0.359 |
| `empty_ratio` | -0.108 | -0.004 | 1.000 | 0.503 | 0.323 | -0.108 |
| `local_ratio` | -0.433 | -0.345 | 0.503 | 1.000 | 0.479 | -0.431 |
| `teu_unit_factor` | -0.266 | -0.055 | 0.323 | 0.479 | 1.000 | -0.266 |
| `teu_total_lag_1` | 0.984 | 0.359 | -0.108 | -0.431 | -0.266 | 1.000 |

## 4. Factorización de Cholesky para Generación Correlacionada
Para generar vectores aleatorios sintéticos $X_{sim} = \mu + L \cdot Z$, donde $Z \sim \mathcal{N}(0, I)$ son perturbaciones Gaussianas estándar ortogonales, calculamos la matriz triangular inferior $L$ tal que $L L^T = \Sigma$.

Esto garantiza que al inducir un choque estocástico sobre el transbordo (`transshipment_ratio`), las variables dependientes (`empty_ratio`, `teu_total`) respondan respetando la covariación histórica real del sistema portuario.

*(Reporte generado automáticamente por `src/simulation/distribution_profiler.py`)*
