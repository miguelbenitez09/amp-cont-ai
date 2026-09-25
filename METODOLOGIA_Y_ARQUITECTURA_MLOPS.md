# Tratado Maestro de Metodología Científica, Arquitectura de Datos y MLOps
## Plataforma Panamá PortOps-AI v1.0

> **Autor:** Desarrollado v1.0 Miguel Benítez  
> **Licencia:** GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria  
> **Ecosistema:** Autoridad Marítima de Panamá (AMP) — Período Histórico 2015–2026 (140 meses)  
> **Repositorio Oficial:** [Panamá PortOps-AI](https://github.com/mbeni/amp-cont-ai)  

---

## 📑 Índice de Contenidos
1. [Formulación Matemática del Problema y Espacio de Variables](#1-formulación-matemática-del-problema-y-espacio-de-variables)
2. [Tratamiento y Limpieza de Datos (Data Cleaning)](#2-tratamiento-y-limpieza-de-datos-data-cleaning)
3. [Estrategia para Campos Vacíos, Faltantes e Incompletos](#3-estrategia-para-campos-vacíos-faltantes-e-incompletos)
4. [Normalización y Estandarización de Variables](#4-normalización-y-estandarización-de-variables)
5. [Anonimización y Protocolos de Datos Sensibles (Compliance Portuario)](#5-anonimización-y-protocolos-de-datos-sensibles-compliance-portuario)
6. [Ingeniería de Características Categóricas](#6-ingeniería-de-características-categóricas)
7. [Ingeniería de Características Marítimas y Temporales (Feature Engineering)](#7-ingeniería-de-características-marítimas-y-temporales-feature-engineering)
8. [Diagnóstico y Tratamiento de Multicolinealidad, Redundancia y Ambigüedad](#8-diagnóstico-y-tratamiento-de-multicolinealidad-redundancia-y-ambigüedad)
9. [Identificación y Control de Variables Confundidoras (*Confounders*)](#9-identificación-y-control-de-variables-confundidoras-confounders)
10. [Benchmarking Multi-Algoritmo y Evaluación de Desempeño](#10-benchmarking-multi-algoritmo-y-evaluación-de-desempeño)
11. [Formulación de Soluciones Operacionales en Negocio Marítimo](#11-formulación-de-soluciones-operacionales-en-negocio-marítimo)
12. [Firma y Atribución Obligatoria](#12-firma-y-atribución-obligatoria)

---

## 1. Formulación Matemática del Problema y Espacio de Variables

El objetivo de la plataforma **Panamá PortOps-AI** es modelar la función generadora de demanda de contenedores en el sistema portuario nacional panameño para las 6 terminales principales:
$$\mathcal{P} = \{\text{Balboa, MIT, PSA, CCT, Cristóbal, Bocas Fruit}\}$$

### A. Variables Dependientes ($Y$ - Target Space)
1. **Variable Dependiente Primaria ($y_{p, t+h}$):**  
   Volumen total mensual de contenedores en unidades equivalentes a veinte pies (**TEUs**) manipulados por el puerto $p \in \mathcal{P}$ en el horizonte temporal $t+h$, con $h \in \{1, 2, \dots, 6\}$ meses:
   $$y_{p, t+h} = \text{TEU\_Total}_{p, t+h} \in \mathbb{R}^+$$
2. **Variable Dependiente Secundaria de Alerta Operacional ($r_{\text{empty}, p, t}$):**  
   Ratio de desbalance de cajas vacías:
   $$r_{\text{empty}, p, t} = \frac{\text{TEU\_Empty}_{p, t}}{\text{TEU\_Full}_{p, t}}$$
   Cuando $r_{\text{empty}} > 0.80$, se activa una alerta estocástica de saturación de patio de almacenamiento.

### B. Variables Independientes ($X$ - Feature Space)
El espacio de características $\mathbf{x}_{p, t} \in \mathbb{R}^{81}$ se particiona en cuatro subespacios ortogonales:
1. **Autorregresivo Endógeno ($X_{\text{AR}}$):**  
   Rezagos temporales $y_{p, t-1}, y_{p, t-2}, y_{p, t-3}, y_{p, t-12}$ y estadísticas móviles calculadas estrictamente sobre ventanas pasadas.
2. **Ratios Operacionales de Dominio ($X_{\text{Ops}}$):**  
   Ratio de transbordo, ratio de carga local y factor de conversión TEU/Unidad física.
3. **Señales Macroeconómicas y Energéticas Exógenas ($X_{\text{Macro}}$):**  
   Ventas nacionales de combustible marino VLSFO en toneladas métricas ($\text{nat\_vlsfo\_sales\_tm}$) y volumen de vehículos RoRo ($\text{nat\_roro\_units}$).
4. **Armónicos Estacionales y Efectos Fijos ($X_{\text{Season}}$):**  
   Descomposiciones cíclicas seno/coseno del mes y trimestre, indicadores binarios de eventos asiáticos (`is_cny`) y variables indicadoras de terminal (*One-Hot Encodings*).

---

## 2. Tratamiento y Limpieza de Datos (Data Cleaning)

Los 353 datasets de la Autoridad Marítima de Panamá (AMP) entre 2015 y 2026 presentan severa heterogeneidad morfológica (tablas de contingencia cruzada vs series longitudinales, separadores mixtos `,` y `;`, codificaciones `utf-8` y `latin-1`).

### Procedimientos de Limpieza Implementados:
1. **Detección y Rectificación de Valores Físicamente Imposibles:**
   - En auditoría preliminar se detectó un valor contable negativo de `-111.0` TEUs en movimientos locales.
   - *Regla de Negocio:* El flujo físico de contenedores es una variable de conteo no negativa $y \ge 0$. Todo ajuste negativo contable se rectifica a $0.0$, documentando la anomalía en el log de auditoría.
2. **Deduplicación Bitemporal de Boletines Acumulativos:**
   - Los informes mensuales de la AMP son acumulativos (el reporte de diciembre reitera los meses de enero a noviembre).
   - Se diseñó un algoritmo bitemporal que indexa cada registro mediante la tupla:
     $$(\text{fecha\_validez}, \text{fecha\_publicación\_archivo})$$
   - El sistema aplica una partición determinista conservando exclusivamente la versión con la marca temporal de publicación más reciente ($\max(\text{timestamp})$), eliminando 14,320 registros redundantes y preservando 8,986 observaciones atómicas limpias.
3. **Filtro de Detección de Outliers Extremos (MAD e IQR):**
   - Para evitar distorsiones por errores tipográficos de digitación gubernamental, se calculó la desviación absoluta de la mediana (*Median Absolute Deviation*):
     $$\text{MAD} = \text{mediana}(|y_i - \tilde{y}|)$$
   - Valores con puntuación modificada de Hampel $|Z_{\text{MAD}}| > 4.5$ fueron sometidos a verificación cruzada contra los boletines PDF oficiales de la AMP antes de su incorporación al Feature Store.

---

## 3. Estrategia para Campos Vacíos, Faltantes e Incompletos

El tratamiento de valores faltantes en series temporales logísticas no puede realizarse con imputaciones estáticas globales (como la media general), ya que distorsionaría la dinámica temporal y causaría fuga de información.

### Protocolo de Imputación Aplicado:
1. **Inexistencia de Datos en Puertos Específicos (E.g. Bocas Fruit Co. sin Zona Libre):**
   - Cuando una categoría no existe por naturaleza física (e.g. puertos bananeros que no manipulan carga de Zona Libre), el valor nulo se imputa determinísticamente como $0.0$, dado que representa ausencia real de operación y no una omisión de registro.
2. **Imputación de Series Temporales Continuas (Lags y Rolling Stats):**
   - Para los primeros meses de la serie histórica (donde $t-12$ no cuenta con historia previa):
     * Se aplica **Backtracking Estacional**: Se utiliza la mediana del mismo mes en los años observados disponibles.
     * En inferencia en producción, se emplea **Forward-Fill Condicional** agrupado por terminal portuaria:
       $$x_{p, t} = x_{p, t-1} \quad \text{si } x_{p, t} \text{ es NaN}$$
3. **Banderas Binarias de Imputación (*Missingness Indicators*):**
   - Para variables exógenas con posibles retrasos de reporte ministerial, se crea una variable binaria auxiliar:
     $$I_{\text{imputed}, j} = \begin{cases} 1 & \text{si la variable } j \text{ fue estimada} \\ 0 & \text{si proviene de reporte primario} \end{cases}$$
   - Esto permite que los algoritmos basados en árboles segreguen la incertidumbre atribuible a datos aproximados.

---

## 4. Normalización y Estandarización de Variables

La elección entre normalización, estandarización o escala original depende de la naturaleza matemática de cada familia algorítmica:

### A. Modelos Basados en Árboles (LightGBM, Random Forest, HistGradientBoosting)
- **Principio:** Los árboles de decisión son **invariantes a transformaciones monótonas** crecientes:
  $$f(X) \iff f(g(X)) \quad \forall g'(X) > 0$$
- **Decisión:** Se preservan las escalas originales de las variables continuas (TEUs, toneladas de bunkering). Esto mantiene la interpretabilidad directa de los umbrales de división (*split points*) en las ramas del árbol (e.g., $\text{TEU\_lag1} \le 185,000$).

### B. Modelos Lineales Regularizados (Ridge / ElasticNet)
- **Principio:** La función de costo lineal con penalización $L_1/L_2$:
  $$J(\beta) = \|y - X\beta\|_2^2 + \lambda_1 \|\beta\|_1 + \lambda_2 \|\beta\|_2^2$$
  es extremadamente sensible a la escala. Si una variable está en millones (TEUs) y otra en decimales ($[0, 1]$, ratios), el coeficiente de la variable pequeña será castigado artificialmente por la penalización $\lambda$.
- **Implementación:** Se construyó un pipeline encapsulado con `StandardScaler`:
  $$Z = \frac{X - \mu_{\text{train}}}{\sigma_{\text{train}}}$$
  calculado estrictamente sobre el conjunto de entrenamiento de cada pliegue temporal (*fit on train, transform on test*), garantizando media 0 y varianza 1.

---

## 5. Anonimización y Protocolos de Datos Sensibles (Compliance Portuario)

En logística internacional y seguridad de la cadena de suministro, la manipulación de datos granulares exige cumplimiento con normativas de confidencialidad comercial y regulaciones internacionales (GDPR / ISPS Code):

### Medidas de Salvaguarda Implementadas:
1. **Agregación Canónica:**
   - La plataforma no almacena identidades individuales de consignatarios (*shippers*), números de conocimiento de embarque (*Bills of Lading - B/L*) ni patentes arancelarias específicas.
   - Los datos se encuentran agregados a nivel macro: **Puerto $\times$ Mes $\times$ Litoral**.
2. **Criptografía de Identificadores (En caso de microdatos de buques/IMO):**
   - Si se ingieren manifiestos con número de registro IMO de buques o códigos de operador de línea naviera (e.g. Maersk, MSC), se aplica una función hash criptográfica irreversible con sal (*salted hash*):
     $$\text{ID}_{\text{anon}} = \text{HMAC-SHA256}(\text{IMO\_Number}, \text{Salt}_{\text{env}})$$
   - Esto permite realizar análisis de recurrencia y *clustering* de navieras sin exponer la identidad de la entidad comercial.

---

## 6. Ingeniería de Características Categóricas

### Codificación de Terminales Portuarias y Litorales:
- Las terminales panameñas presentan profundas asimetrías de infraestructura y conectividad oceánica:
  - **Litoral Pacífico:** Balboa, PSA (orientadas a rutas transpacíficas con Asia y Cabotaje Sudamérica Oeste).
  - **Litoral Atlántico:** MIT, Cristóbal, CCT, Bocas Fruit (orientadas a transbordo hacia Costa Este EE.UU., Europa y el Caribe).
- **Procedimiento:** Se implementa **One-Hot Encoding exhaustivo**:
  $$p_i \in \{0, 1\} \quad \forall i \in \{1, \dots, K\}$$
- **Garantía en Tiempo de Inferencia:** Para evitar errores por discrepancia de columnas (*schema mismatch*) durante la predicción en tiempo real, el microservicio FastAPI valida y alinea la matriz de características con el esquema canónico guardado en el artefacto de entrenamiento (`feature_cols`), rellenando terminales no activas con $0$.

---

## 7. Ingeniería de Características Marítimas y Temporales (Feature Engineering)

Se diseñaron 81 variables predictivas estructuradas en tres módulos modulares con **garantía matemática de Zero Data Leakage**:

### A. Armónicos Cíclicos Estacionales
Para preservar la continuidad topológica entre diciembre ($m=12$) y enero ($m=1$):
$$\text{mes}_{\sin} = \sin\left(\frac{2\pi \cdot m}{12}\right), \quad \text{mes}_{\cos} = \cos\left(\frac{2\pi \cdot m}{12}\right)$$
$$\text{trimestre}_{\sin} = \sin\left(\frac{2\pi \cdot q}{4}\right), \quad \text{trimestre}_{\cos} = \cos\left(\frac{2\pi \cdot q}{4}\right)$$

### B. Banderas de Dominio Marítimo Internacional
- **Efecto Año Nuevo Chino (`is_cny_impact_month`):** Bandera binaria activa en enero y febrero ($m \in \{1, 2\}$) que captura el cese de operaciones de las fábricas en China y el posterior incremento de salidas en blanco (*blank sailings*).
- **Temporada Alta Navideña (`is_peak_shipping_season`):** Bandera binaria activa en agosto, septiembre y octubre ($m \in \{8, 9, 10\}$) correspondiente al adelanto de inventarios para el comercio minorista occidental.

### C. Ratios Operacionales de Estructura Portuaria
1. **Ratio de Trasbordo:**  
   $$r_{\text{trans}} = \frac{\text{TEU\_Transshipment}}{\text{TEU\_Total}}$$
2. **Ratio de Vacíos vs Llenos:**  
   $$r_{\text{empty}} = \frac{\text{TEU\_Empty}}{\text{TEU\_Full}}$$
3. **Factor de Conversión TEU/Unidad:**  
   $$f_{\text{teu/unit}} = \frac{\text{TEU\_Total}}{\text{Unit\_Total}}$$
   Indica el tamaño modal predominante: valores cercanos a $2.0$ denotan predominancia absoluta de contenedores FEU de 40 pies; valores cercanos a $1.0$ reflejan cajas TEU de 20 pies (e.g. carga pesada mineral o agrícola).

### D. Lags y Estadísticas Rodantes sin Fuga
Todos los rezagos y agregaciones móviles se computan sobre la serie desplazada:
$$\mathbf{y}_{\text{shifted}} = \text{shift}(1)$$
- **Rezagos Puntuales:** $t-1, t-2, t-3, t-12$.
- **Ventanas Móviles (3 y 6 meses):** Media móvil, desviación estándar móvil, valores mínimos y máximos.
- **Medias Móviles Ponderadas Exponencialmente (EWMA):**
  $$\text{EWMA}_t = \alpha y_{t-1} + (1 - \alpha) \text{EWMA}_{t-1}$$
  con factores de amortiguamiento para capturar tendencias de corto plazo ($\text{span}=3$) y mediano plazo ($\text{span}=6$).

---

## 8. Diagnóstico y Tratamiento de Multicolinealidad, Redundancia y Ambigüedad

Las series de tiempo con múltiples rezagos autorregresivos sufren intrínsecamente de multicolinealidad: $y_{t-1}$ está altamente correlacionada con $y_{t-2}$ y con las medias móviles.

### Matriz de Diagnóstico Cuantitativo:
En la auditoría del Feature Store se detectaron las siguientes correlaciones bivariadas elevadas:
- $\text{Corr}(\text{teu\_total\_lag\_1}, \text{teu\_total\_lag\_2}) = 0.9741$
- $\text{Corr}(\text{teu\_total\_lag\_2}, \text{teu\_total\_lag\_3}) = 0.9743$
- $\text{Corr}(\text{teu\_total\_lag\_1}, \text{teu\_total\_lag\_3}) = 0.9615$

### Cálculo del Factor de Inflación de la Varianza (VIF):
$$\text{VIF}_j = \frac{1}{1 - R_j^2}$$
donde $R_j^2$ es el coeficiente de determinación al regresar la característica $x_j$ sobre todas las demás características independientes.
- **Ratios Operacionales Desacoplados (Excelente):**
  - $\text{VIF}(\text{transshipment\_ratio}) = 1.53$
  - $\text{VIF}(\text{empty\_ratio}) = 1.58$
  - $\text{VIF}(\text{teu\_unit\_factor}) = 1.36$
  - $\text{VIF}(\text{is\_cny}) = 1.39$
- **Lags Autorregresivos Continuos:** Presentan $\text{VIF} > 15.0$ debido a la inercia temporal de las terminales.

### Estrategia de Mitigación:
1. **Para Modelos de Árboles (LightGBM / Random Forest):**
   Los algoritmos basados en árboles no se ven afectados numéricamente por la multicolinealidad estricta para la predicción, ya que seleccionan el feature con mayor ganancia de información en cada nodo.
2. **Para Modelos Lineales:**
   La multicolinealidad desestabiliza la inversión de la matriz $(X^T X)^{-1}$. Por ello, el modelo lineal simple colapsó ($\text{WAPE} > 1,000\%$). La solución implementada consistió en aplicar **penalización Ridge $L_2$ ($\alpha = 100.0$)** combinada con `StandardScaler`, lo que condiciona los valores propios de la matriz Hessian:
   $$\hat{\beta}_{\text{Ridge}} = (X^T X + \lambda I)^{-1} X^T y$$

---

## 9. Identificación y Control de Variables Confundidoras (*Confounders*)

Una variable confundidora $Z$ afecta simultáneamente a la variable independiente predictora $X$ y al resultado de demanda portuaria $Y$, creando correlaciones espurias si no se controla adecuadamente.

```
       [ Confounder (Z) ]
         /           \
        v             v
[ Predictor (X) ] ---> [ TEU Demand (Y) ]
```

### Confundidores Clave en el Sistema Portuario Panameño:

| Variable Confundidora ($Z$) | Efecto sobre Predictor ($X$) | Efecto sobre Demanda ($Y$) | Tratamiento Implementado |
| :--- | :--- | :--- | :--- |
| **1. Estacionalidad Global (Año Nuevo Chino)** | Reduce temporalmente las ventas de combustible marino ($X_{\text{bunker}}$). | Paraliza el flujo de contenedores de trasbordo ($Y$). | Desacoplado mediante armónicos ortogonales $\sin/\cos$ y bandera `is_cny`. Evita que el modelo atribuya la caída a una pérdida de competitividad de la terminal. |
| **2. Restricción Hídrica del Canal (Sequía El Niño)** | Aumenta el costo de bunkering y altera los tiempos de recalada. | Reduce el calado de buques Neopanamax de 50 a 44 pies, desviando carga hacia otros hubs. | Incorporación de series macro de bunkering bitemporales y variables fijas de litoral (Atlántico vs Pacífico). |
| **3. Capacidad Fisiológica de Terminal (Infraestructura / Grúas STS)** | Condiciona los volúmenes históricos rezagados ($y_{t-1}$). | Establece un límite superior rígido en la productividad por muelle. | Modelo de Efectos Fijos mediante One-Hot Encoding por terminal, permitiendo que cada puerto tenga su propio intercepto y sensibilidad. |

---

## 10. Benchmarking Multi-Algoritmo y Evaluación de Desempeño

Se evaluaron cuatro arquitecturas de aprendizaje supervisado bajo el mismo esquema de **Expanding Window Backtesting** (3 particiones temporales: 2022, 2023 y 2024–2026):

### Tabla de Desempeño Comparativo:

| Algoritmo | Rol MLOps | WAPE Promedio (%) | $R^2$ Score | RMSE (TEUs) | Latencia Media (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **LightGBM Quantile (P10/P50/P90)** | 🏆 **Champion** | **9.11%** | **0.9594** | **15,080** | 13.28 ms |
| **Random Forest Regressor** | 🥈 Challenger | **9.10%** | **0.9588** | 15,085 | 4.58 ms |
| **HistGradientBoosting** | 🥉 Challenger | **9.78%** | **0.9545** | 15,853 | 70.30 ms |
| **Ridge Regularized Linear (Pipeline)** | Baseline | >1,000%* | -0.0188* | 2,646M* | 0.19 ms |

*\*Nota: El modelo lineal colapsa en la partición 3 debido a la fuerte multicolinealidad de los 81 rezagos continuos en horizontes largos.*

### Hallazgos de Modelado:
1. **LightGBM como Champion de Producción:**  
   Ofrece el balance óptimo entre precisión (WAPE 9.11%), robustez ante datos de cola pesada y la capacidad de entregar **estimaciones por cuantiles directos (P10, P50, P90)** mediante optimización de la función de pérdida Pinball:
   $$L_\alpha(y, \hat{y}) = \max(\alpha(y - \hat{y}), (1 - \alpha)(\hat{y} - y))$$
2. **Random Forest como Challenger de Alta Velocidad:**  
   Logró un WAPE prácticamente idéntico (9.10%) con una latencia de inferencia ultrarrápida de 4.58 ms, convirtiéndose en el candidato óptimo para microservicios de ultra-baja latencia.

---

## 11. Formulación de Soluciones Operacionales en Negocio Marítimo

Las salidas de la plataforma se traducen directamente en políticas logísticas activas:

1. **Planificación de Cuadrillas y Grúas STS (Basado en P90):**
   - El percentil 90 ($\text{P90}$) define el dimensionamiento de capacidad pico. Cuando el pronóstico P90 supera el 85% de la capacidad instalada, la gerencia de operaciones portuarias activa turnos adicionales de operadores de grúas pórtico para evitar congestión de buques en fondeadero.
2. **Mitigación del Desbalance de Cajas Vacías (Basado en $r_{\text{empty}}$):**
   - Cuando el modelo proyecta un ratio de cajas vacías superior a $0.80$, se disparan órdenes automáticas de coordinación con navieras para fletar buques de evacuación de vacíos (*sweeper vessels*) hacia centros de manufactura asiáticos.
3. **Planes de Contingencia ante Shocks de Sequía (Basado en Stress Testing Monte Carlo):**
   - El motor de simulación calcula el **Value at Risk (VaR 95%)** y el **Expected Shortfall (CVaR 95%)**, permitiendo a las autoridades establecer reservas financieras de estabilización ante caídas de volumen provocadas por restricciones de calado en el Canal de Panamá.

---

## 12. Firma y Atribución Obligatoria

Toda la arquitectura, ingeniería de datos, formulación matemática, pipelines de modelado, motor estocástico e interfaz visual han sido diseñados e implementados bajo los estándares más estrictos de MLOps:

```text
================================================================================
                    PANAMÁ PORTOPS-AI — PLATAFORMA MLOPS
                    Desarrollado v1.0 Miguel Benítez
                    Licencia: GNU General Public License v3.0 (GPL-3.0)
================================================================================
```

Cualquier uso, reproducción, publicación científica o despliegue comercial derivado de esta obra debe preservar obligatoriamente este reconocimiento y la licencia copyleft de código abierto.
