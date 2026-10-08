# Guía de Uso del Sistema y Tutorial Interactivo Inmersivo
## Plataforma Soberana de Inteligencia Portuaria, Tráfico del Canal de Panamá y Arancel Nacional SAC (PortOps-AI v1.0.0)

**Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (Universidad Tecnológica de Panamá - UTP)**  
*Licencia Pública General de GNU v3.0 (GNU GPL-3.0) con Atribución Obligatoria (Sección 7).*  
*Fecha de Emisión: Octubre 2026 • Estado: Producción Operativa / Verificación Integral*

---

## 1. Resumen Ejecutivo y Misión Tecnológica

**Panamá PortOps-AI** es un ecosistema industrial de inteligencia logística, benchmarking multi-algoritmo y simulación estocástica diseñado específicamente para el complejo marítimo e interoceánico de la República de Panamá.

### Principios Rectores:
1. **Soberanía y Código Abierto**: Elimina la dependencia de licencias comerciales extranjeras costosas, proporcionando a PyMEs logísticas, agencias navieras, operadores de terminales e instituciones públicas (AMP, ACP, ANA, INEC) una suite analítica de nivel industrial bajo licencia GNU GPL-3.0.
2. **Cero Datos Sintéticos (Zero-Mock Policy)**: Cada cifra, métrica, pronóstico y registro visualizado en el sistema proviene directamente de microdatos oficiales reales procesados en el Lakehouse Medallion (1997–2026), abarcando más de **8.74 GB de almacenamiento**, **23,640+ archivos físicos** y **14.2M+ transacciones aduaneras y portuarias**.
3. **Seguridad y Trazabilidad Criptográfica WORM**: Registro inmutable de transacciones, consultas fiscales e inferencias con encadenamiento de bloques SHA-256 (Write-Once-Read-Many), garantizando no repudio bajo la Ley 6 de 2002 (Transparencia) y privacidad conforme a la Ley 81 de 2019 (Datos Personales).

---

## 2. Experiencia de Usuario y Recorrido Guiado Interactivo

Para asegurar que cualquier operador, auditor o analista domine el portal sin curva de aprendizaje empinada, PortOps-AI incorpora un **Motor de Recorrido Guiado Interactivo (`PortOpsInteractiveTour`)**:

```
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 🚀 Iniciar Tour Guiado (Navbar / Hero Button)                          │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 1. Hub Marítimo & Plataforma Soberana (.landing-hero)                  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 2. Idiomas & Esquemas de Color Náuticos (#nav-lang-select / Temas)    │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 3. Centro de Seguridad IAM & Roles RBAC (#btn-auth-iam, 31 Capacidades)│
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 4. Integridad Criptográfica WORM SHA-256 (#hud-worm-status)            │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 5. Enjambre Agéntico & Razonamiento CoT (#tab-btn-cot)                 │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 6. Aduanas, RAG Arancelario & Lakehouse 5D (#tab-btn-customs)          │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 7. Inferencia Cuantílica & Escenarios What-If (tab-forecast)           │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ 8. Simulación Estocástica & Riesgo Marítimo (tab-simulation)           │
 └────────────────────────────────────────────────────────────────────────┘
```

### Activación del Tour:
* **Botón en Encabezado**: Haz clic en el botón `🚀 Tour Guiado` ubicado en la barra superior.
* **Botón en Hero Banner**: Haz clic en el botón `🚀 Iniciar Tour Interactivo` en la sección principal.
* **Desde Consola / Automatización**: Invoca en cualquier momento `window.PortOpsTour.start()`.

### Atajos de Teclado del Tour:
* **Flecha Derecha (`→`) o Enter**: Avanzar al siguiente paso explicativo.
* **Flecha Izquierda (`←`)**: Retroceder al paso anterior.
* **Escape (`Esc`)**: Cerrar o pausar el recorrido guiado en cualquier momento.

### Diseño Inclusivo y Accesibilidad (WCAG 2.2 Nivel AA):
* **Anillo de Foco Visual Pulsante**: Un halo de luz neón con `cubic-bezier(0.16, 1, 0.3, 1)` y difuminado de fondo (`backdrop-filter: blur(3px)`) resalta dinámicamente el componente en análisis.
* **Contraste Semántico**: Las 6 paletas de colores (Atlántico Cian, Radar Ámbar, Cuenca Esmeralda, Titanio Táctico, Pacífico Sunset y Midnight Cobalt) superan una relación de contraste mínima de 4.5:1 para texto normal y 3:1 para controles activos.
* **Navegación por Teclado (`:focus-visible`)**: Cada tarjeta interactiva, botón y campo de formulario cuenta con un anillo exterior de 2px con desfase de 3px, permitiendo la operación fluida sin mouse.

---

## 3. Guía Modular por Componentes de la Plataforma

### 3.1. Barra de Navegación y HUD de Telemetría (Header)
* **Selector de Idioma**: Soporte trilingüe nativo (Español 🇪🇸, English 🇺🇸, Português 🇧🇷) con sincronización reactiva en tiempo real sin recargar la página.
* **Selector de Paleta Visual**: 6 temas optimizados para centros de control portuario diurnos y nocturnos.
* **Centro de Autenticación e IAM**:
  * Gestión de tokens JWT / Bearer con rotación automática.
  * Autenticación Multifactor MFA RFC 6238 TOTP (Google Authenticator, Microsoft Authenticator, FreeOTP).
  * Matriz de 31 capacidades de acceso segmentadas en 4 roles (`Invitado`, `Operador Portuario`, `Científico de Datos`, `Administrador / Auditor`).
* **Insignia WORM SHA-256**: Verifica la altura de bloques del ledger criptográfico y el estado de la cadena inmutable.
* **Telemetría de Latencia**: Monitorización en milisegundos de la latencia neta de red e inferencia sub-segundo.

---

### 3.2. Pestaña 0: Inicio & Visión General (`tab-landing`)
* **Contexto de Misión**: Explicación de la transferencia tecnológica a PyMEs y grandes terminales.
* **Cuadrícula de 4 Pilares Operativos**:
  1. *PyMEs & Comercio Exterior*: Diagnósticos de viabilidad arancelaria y costos DUA/ITBMS.
  2. *6 Terminales Portuarias*: Balboa, Cristóbal, Manzanillo (MIT), Colón Container Terminal (CCT), PSA Panama International Terminal (Rodman) y Bocas Fruit Co.
  3. *Investigación & MLOps*: Torneo de 8 algoritmos con Zero Lookahead y diagnóstico Durbin-Watson.
  4. *Transparencia & Gobernanza WORM*: Cumplimiento cívico de la Ley 6 de 2002 y anonimización según Ley 81 de 2019.
* **Resumen Cuantitativo en Tiempo Real**: Estadísticas consolidadas directamente del almacenamiento físico del Lakehouse.

---

### 3.3. Pestaña 1: Enjambre Agéntico & Razonamiento CoT (`tab-cot-swarm`)
* **Almas Criptográficas (Soul Cards)**:
  * 🛃 **Agente Aduanal**: Especialista en el Arancel Nacional del SAC, liquidación DAI, ITBMS, tasas aduaneras y regulaciones de la ANA.
  * 🚢 **Agente Logístico**: Experto en congestión de patios, tiempos de fondeo, ventanas de atraque y grúas STS.
  * 📊 **Agente Cuantílico**: Modelado de incertidumbre P10/P50/P90, matrices de covarianza y desbalance de contenedores vacíos.
  * 🛡️ **Agente de Seguridad**: Verificación de firmas criptográficas, detección de inyecciones de prompt y auditoría WORM.
* **Guardrails Anti-Inyección de Prompts**:
  * Filtrado semántico en dos capas que bloquea jailbreaks, evasiones de rol y comandos maliciosos, preservando consultas legítimas de comercio exterior.
* **Trazabilidad CoT (Chain-of-Thought)**:
  * Visualización paso a paso de los 5 hitos operacionales:
    1. *Validación de Intención y Contexto Logístico*
    2. *Recuperación Aumentada RAG (Arancel SAC & Histórico DUA)*
    3. *Evaluación de Reglas y Normativas Panameñas (Leyes 6, 56, 81)*
    4. *Cálculo Cuantílico y Simulación de Impacto*
    5. *Síntesis Ejecutiva con Citas Jurídicas y Hash Anti-Tamper*

---

### 3.4. Pestaña 2: Aduanas, RAG Arancelario & Lakehouse Medallion (`tab-customs-lakehouse`)
* **Buscador Semántico RAG**:
  * Búsqueda en lenguaje natural sobre las 27,764 subpartidas del Sistema Arancelario Centroamericano (SAC).
  * Recuperación inmediata de descripciones oficiales, notas de capítulo, tarifas de DAI (Derecho Arancelario a la Importación) e ITBMS (7%, 10%, 15%).
* **Calculadora Fiscal de Declaración DUA (ANA)**:
  * Ingreso de valor FOB, flete internacional y seguro marítimo para calcular el valor CIF (Cost, Insurance and Freight).
  * Desglose instantáneo de:
    $$\text{DAI} = \text{CIF} \times \text{Tarifa}_{\text{DAI}}$$
    $$\text{Base ITBMS} = \text{CIF} + \text{DAI}$$
    $$\text{ITBMS} = \text{Base ITBMS} \times \text{Tarifa}_{\text{ITBMS}}$$
    $$\text{Total Tributos} = \text{DAI} + \text{ITBMS} + \text{Tasa de Servicio}$$
* **Validador de Contenedores ISO 6346**:
  * Comprobación del dígito verificador mediante algoritmo de ponderación modular:
    $$\sum_{i=1}^{10} v_i \cdot 2^{i-1} \pmod{11}$$
  * Identificación de tipo de contenedor (Dry 20'/40', High Cube, Reefer refrigerado, Flat Rack, Open Top).

---

### 3.5. Pestaña 3: Pronóstico Cuantílico & Simulación What-If (`tab-forecast`)
* **Inferencia Cuantílica Sub-Segundo**:
  * Selección de terminal portuaria y horizonte predictivo (1 a 6 meses).
  * Generación de bandas de predicción calibradas:
    * $P_{10}$ (Escenario de Mínima Demanda / Suelo Operativo)
    * $P_{50}$ (Mediana Estadística Esperada / Base Operativa)
    * $P_{90}$ (Escenario de Alta Demanda / Techo de Capacidad de Patio)
* **Simulador de Escenarios What-If**:
  * Control deslizante de variación en precio de búnker marino VLSFO ($\pm 30\%$).
  * Control deslizante de desvío de transbordos marítimos interoceánicos ($\pm 25\%$).
  * Recálculo instantáneo de la demanda esperada en TEUs y estimación del porcentaje de contenedores vacíos con semáforo de saturación.

---

### 3.6. Pestaña 4: Comparativa Multi-Algoritmo & MLOps (`tab-benchmark`)
* **Torneo Determinista de Modelos**:
  * Evaluación exhaustiva de 8 familias algorítmicas sobre series históricas:
    1. *LightGBM Quantile Regressor* (Campeón de Producción)
    2. *CatBoost Multi-Quantile*
    3. *Random Forest Ensembled*
    4. *XGBoost Monotonic*
    5. *Prophet Bayesian Time Series*
    6. *SARIMAX con Regresores Externos*
    7. *Exponential Smoothing (Holt-Winters)*
    8. *DeepAR / Temporal Fusion Transformers (TFT)*
* **Métricas Formales de Evaluación**:
  * Pinball Loss cuantílico ponderado:
    $$\mathcal{L}_q(y, \hat{y}) = \max(q(y - \hat{y}), (q-1)(y - \hat{y}))$$
  * WAPE (Weighted Absolute Percentage Error), RMSE y Cobertura Empírica de Intervalo (PICP).

---

### 3.7. Pestaña 5: Simulación Estocástica & Riesgo Marítimo (`tab-simulation`)
* **Simulación Monte Carlo (5,000 Trayectorias)**:
  * Modelado de caminos estocásticos de movimiento de contenedores bajo procesos de difusión con saltos (Jump-Diffusion).
  * Métricas de riesgo financiero y operativo: Value at Risk (VaR al 95%) y Conditional Value at Risk (CVaR).
* **Teoría de Valores Extremos (EVT Gumbel)**:
  * Modelado de colas pesadas y riesgo de sequía extrema en el Lago Gatún que restrinja el calado del Canal de Panamá por debajo de 44 pies.
* **Teoría de Colas Portuarias $M/M/c$**:
  * Estimación de tiempos de espera en fondeadero, factor de utilización de muelles $\rho = \frac{\lambda}{c \mu}$ y probabilidad de congestión según número de grúas STS activas.

---

### 3.8. Pestaña 6: Gobernanza, Seguridad IAM & Auditoría WORM (`tab-security-iam`)
* **Inspección de Bloques WORM**:
  * Visualización en vivo de la altura de bloques, timestamp UTC, autor de la transacción, tipo de operación y hash SHA-256 encadenado:
    $$H_n = \text{SHA-256}(H_{n-1} \parallel \text{Payload}_n \parallel \text{Timestamp}_n)$$
* **Simulador y Verificador de Roles**:
  * Prueba de degradación y elevación de permisos según capacidades RBAC para validar que las pantallas restringidas oculten o bloqueen acciones no autorizadas.

---

## 4. Guía de Integración API para Desarrolladores

Para consumir el motor de inferencia directamente desde sistemas externos (ERP de navieras, TOS de terminales, portales gubernamentales), la plataforma proporciona generadores de código dinámicos adaptados al origen actual de la aplicación (`window.location.origin`):

### Petición cURL:
```bash
# Inferencia Cuantílica para Puerto Balboa (Horizonte 3 Meses)
curl -X POST "http://127.0.0.1:8000/predict" \
  -H "Authorization: Bearer $AMP_API_SECRET_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "port": "Puerto Balboa",
    "horizon_months": 3,
    "algorithm": "ensemble",
    "what_if_bunkering_shift_pct": 0.0,
    "what_if_transshipment_shift_pct": 0.0
  }'
```

### Script Python:
```python
import requests

url = "http://127.0.0.1:8000/predict"
headers = {
    "Authorization": "Bearer <YOUR_AMP_API_SECRET_KEY>",
    "Content-Type": "application/json"
}
payload = {
    "port": "Puerto Balboa",
    "horizon_months": 3,
    "algorithm": "ensemble",
    "what_if_bunkering_shift_pct": 0.0,
    "what_if_transshipment_shift_pct": 0.0
}

response = requests.post(url, json=payload, headers=headers, timeout=10.0)
response.raise_for_status()
data = response.json()

print(f"Puerto: {data['port']} | Latencia: {data['latency_ms']:.2f} ms")
for pred in data["predictions"]:
    print(f"  Mes {pred['horizon_step']} ({pred['target_month']}): "
          f"P50={pred['pred_p50_teu']:,.0f} TEUs | "
          f"Rango=[{pred['pred_p10_teu']:,.0f} - {pred['pred_p90_teu']:,.0f}]")
```

---

## 5. Preguntas Frecuentes y Resolución de Problemas

1. **¿Por qué las predicciones muestran bandas P10 y P90 en lugar de un solo número?**  
   En la logística marítima, las proyecciones puntuales crean una falsa sensación de certeza. Las bandas cuantílicas reflejan la incertidumbre operativa real causada por fluctuaciones de mercado, condiciones meteorológicas y factores geopolíticos.
2. **¿Cómo se garantiza que no haya datos inventados o sintéticos?**  
   Todas las tablas y series temporales provienen de los datasets oficiales de la Autoridad Marítima de Panamá (AMP) e INEC. El supervisor autónomo (`tools/scrapers/comext_autonomous_supervisor.py`) verifica cada lote con sumas de comprobación SHA-256 antes de incorporarlo al Lakehouse.
3. **¿Cómo reportar incidentes o proponer nuevas funcionalidades?**  
   El repositorio oficial en GitHub se encuentra sincronizado bajo la rama `main`. Toda modificación debe mantener la atribución legal al autor y cumplir con la suite completa de pruebas unitarias y de integración (`pytest` y `go test`).

---

*Manual de Operaciones y Referencia Técnica Oficial • PortOps-AI v1.0.0*  
*Desarrollado v1.0.0 Miguel Benítez (UTP) - GNU GPL-3.0*
