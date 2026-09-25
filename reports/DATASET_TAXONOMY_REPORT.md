# Reporte de Taxonomía y Clasificación Exhaustiva de Datasets AMP

## 1. Visión General
Se han inspeccionado y clasificado algorítmicamente un total de **353 datasets** obtenidos de la Autoridad Marítima de Panamá.

### Métricas de Distribución por Dominio Operativo
| Dominio de Negocio | Cantidad de Datasets | % del Total |
| :--- | :--- | :--- |
| `LOGISTICA_CONTENEDORES` | 177 | 50.1% |
| `BUNKERING_COMBUSTIBLE_MARINO` | 60 | 17.0% |
| `INDICADORES_MACRO_PORTUARIOS` | 59 | 16.7% |
| `CARGA_RODANTE_RORO` | 51 | 14.4% |
| `REGISTRO_NAVAL_PANAMA` | 5 | 1.4% |
| `GENTE_DE_MAR` | 1 | 0.3% |

### Distribución por Estructura y Orientación Tabular
| Tipo de Estructura | Cantidad | Descripción |
| :--- | :--- | :--- |
| `VERTICAL_WIDE_PORTS_AS_COLUMNS` | 279 | Puertos en columnas y meses en filas |
| `GENERIC_TABULAR` | 48 | Puertos en columnas y meses en filas |
| `HORIZONTAL_WIDE_MONTHS_AS_COLUMNS` | 26 | Meses en columnas (requiere unpivot/melt) |

### Calidad Técnica: Encodings y Delimitadores
- **Encodings:** {'latin-1': 332, 'utf-8': 21}
- **Delimitadores:** {',': 269, ';': 84}

## 2. Detalle Exhaustivo por Dominio Operativo

### Dominio: `BUNKERING_COMBUSTIBLE_MARINO` (60 datasets)

- **Unidad de Medida Principal:** TONELADAS_METRICAS_Y_BARRILES
- **Sub-contextos identificados:** ['EMBARQUE_SEGÚN_LITORAL', 'VENTAS_POR_BARCAZA_LITORAL']
- **Tamaño total:** 68.26 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-embarque-de-combustible-marino-abril-2021` | Embarque de Combustible según Litoral | 4 | 6 |
| `amp-embarque-de-combustible-marino-agosto-202` | Embarque de Combustible según Litoral | 4 | 10 |
| `amp-embarque-de-combustible-marino-diciembre-` | Embarque de Combustible según Litoral | 4 | 14 |
| `amp-embarque-de-combustible-marino-enero-2024` | Embarque de Combustible según Litoral | 4 | 14 |
| `amp-embarque-de-combustible-marino-enero-agos` | Embarque de Combustible según Litoral | 4 | 10 |

---

### Dominio: `CARGA_RODANTE_RORO` (51 datasets)

- **Unidad de Medida Principal:** UNIDADES
- **Sub-contextos identificados:** ['VEHICULOS_POR_PUERTO']
- **Tamaño total:** 57.40 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-movimiento-de-carga-de-comercio-exterior-` | Movimiento de Vehículos (Desembarque y Embarque) | 40 | 4 |
| `amp-movimiento-de-carga-de-comercio-exterior-` | Movimiento de Vehículos (Desembarque y Embarque) | 42 | 4 |
| `amp-movimiento-de-vehiculo-abril-2021.csv` | Movimiento de Vehículos (Desembarque y Embarque) | 12 | 10 |
| `amp-movimiento-de-vehiculo-agosto-2021.csv` | Movimiento de Vehículos (Desembarque y Embarque) | 24 | 10 |
| `amp-movimiento-de-vehiculo-marzo-2021.csv` | Movimiento de Vehículos (Desembarque y Embarque) | 9 | 10 |

---

### Dominio: `GENTE_DE_MAR` (1 datasets)

- **Unidad de Medida Principal:** LICENCIAS_Y_CARNETS
- **Sub-contextos identificados:** ['TITULACION_Y_CERTIFICACION']
- **Tamaño total:** 0.76 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-ingresos-por-titulacion-de-la-gente-de-ma` | Titulaciones Marítimas STCW | 21 | 5 |

---

### Dominio: `INDICADORES_MACRO_PORTUARIOS` (59 datasets)

- **Unidad de Medida Principal:** MULTI_METRICA
- **Sub-contextos identificados:** ['SISTEMA_PORTUARIO_NACIONAL']
- **Tamaño total:** 8267.72 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-indicador-de-tramite-de-documentos-de-reg` | Consolidado Portuario (Carga TM, Cruceros, Cabotaje) | 3 | 7 |
| `amp-indicador-de-tramite-de-documentos-diciem` | Consolidado Portuario (Carga TM, Cruceros, Cabotaje) | 36 | 7 |
| `amp-indicador-maritimo-portuario-agosto-2021.` | Consolidado Portuario (Carga TM, Cruceros, Cabotaje) | 24 | 10 |
| `amp-indicador-maritimo-portuario-diciembre-20` | Consolidado Portuario (Carga TM, Cruceros, Cabotaje) | 36 | 10 |
| `amp-indicador-maritimo-portuario-diciembre-20` | Consolidado Portuario (Carga TM, Cruceros, Cabotaje) | 36 | 10 |

---

### Dominio: `LOGISTICA_CONTENEDORES` (177 datasets)

- **Unidad de Medida Principal:** TEU
- **Sub-contextos identificados:** ['DESTINO_OPERATIVO', 'TOTAL_PUERTO', 'TIPO_LLENOS_VACIOS']
- **Tamaño total:** 343.17 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-contenedores-en-el-spn-por-destino-en-teu` | Contenedores DESTINO_OPERATIVO (TEU) | 1 | 20 |
| `amp-movimiento-de-contenedores-en-el-spn-en-t` | Contenedores TOTAL_PUERTO (TEU) | 36 | 8 |
| `amp-movimiento-de-contenedores-en-el-spn-en-t` | Contenedores TOTAL_PUERTO (TEU) | 12 | 8 |
| `amp-movimiento-de-contenedores-en-el-spn-en-t` | Contenedores TOTAL_PUERTO (TEU) | 24 | 8 |
| `amp-movimiento-de-contenedores-en-el-spn-en-t` | Contenedores TOTAL_PUERTO (TEU) | 36 | 8 |

---

### Dominio: `REGISTRO_NAVAL_PANAMA` (5 datasets)

- **Unidad de Medida Principal:** TRAMITES_Y_DOCUMENTOS
- **Sub-contextos identificados:** ['TITULOS_E_HIPOTECAS']
- **Tamaño total:** 5.97 KB

| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |
| :--- | :--- | :--- | :--- |
| `amp-registro-de-desembarque-de-peces-en-libra` | Trámites Registrales de Naves y Certificados | 12 | 15 |
| `amp-registro-de-desembarque-de-peces-en-libra` | Trámites Registrales de Naves y Certificados | 12 | 15 |
| `amp-registro-de-desembarque-de-peces-en-libra` | Trámites Registrales de Naves y Certificados | 12 | 15 |
| `amp-registro-de-desembarque-de-peces-por-puer` | Trámites Registrales de Naves y Certificados | 10 | 14 |
| `amp-registro-de-desembarque-de-peces-por-puer` | Trámites Registrales de Naves y Certificados | 10 | 14 |

---

