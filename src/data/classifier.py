"""
Dataset Taxonomy and Classification Engine.
Classifies all AMP datasets by operational context, structural type, temporal nature, and schema.
Adheres to MLOps Masterclass Section 1.3 & 16: Understanding data source heterogeneity.
"""

import os
import re
import json
import glob
from pathlib import Path
from typing import Dict, List, Any, Tuple
import pandas as pd
from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
REPORTS_DIR = PROJECT_ROOT / "reports"

class DatasetClassifier:
    """
    Analyzes, parses, and classifies raw maritime datasets into standardized
    functional domains, operational contexts, and structural schemas.
    """

    def __init__(self, raw_dir: Path = RAW_DIR, catalog_path: Path = METADATA_DIR / "datasets_catalog.csv"):
        self.raw_dir = raw_dir
        self.catalog_path = catalog_path
        self.catalog_df = pd.read_csv(catalog_path) if catalog_path.exists() else pd.DataFrame()

    @staticmethod
    def detect_encoding_and_delimiter(filepath: Path) -> Tuple[str, str]:
        """Inspects byte stream to detect encoding and delimiter."""
        with open(filepath, "rb") as f:
            raw = f.read(4096)
        
        # Test UTF-8 vs Latin-1
        try:
            raw.decode("utf-8")
            enc = "utf-8"
        except UnicodeDecodeError:
            enc = "latin-1"
            
        sample = raw.decode(enc, errors="replace")
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        delim = ";" if ";" in first_line else ("," if "," in first_line else "\t")
        return enc, delim

    @staticmethod
    def classify_context(title: str, slug: str) -> Dict[str, str]:
        """
        Classifies dataset into business domain, sub-context, and operational scope.
        """
        text = f"{title} {slug}".lower()
        
        # Container movements
        if "contenedor" in text:
            domain = "LOGISTICA_CONTENEDORES"
            if "destino" in text:
                sub_context = "DESTINO_OPERATIVO"
                unit = "TEU" if "teu" in text else "UNIDADES"
            elif "tipo" in text:
                sub_context = "TIPO_LLENOS_VACIOS"
                unit = "TEU" if "teu" in text else "UNIDADES"
            elif "teu" in text:
                sub_context = "TOTAL_PUERTO"
                unit = "TEU"
            else:
                sub_context = "TOTAL_PUERTO"
                unit = "UNIDADES"
            scope = f"Contenedores {sub_context} ({unit})"
            
        # Bunkering / Marine Fuel
        elif "combustible" in text or "barcaza" in text:
            domain = "BUNKERING_COMBUSTIBLE_MARINO"
            unit = "TONELADAS_METRICAS_Y_BARRILES"
            if "venta" in text or "barcaza" in text:
                sub_context = "VENTAS_POR_BARCAZA_LITORAL"
                scope = "Venta de Bunker por Barcazas (Pacífico y Atlántico)"
            elif "embarque" in text:
                sub_context = "EMBARQUE_SEGÚN_LITORAL"
                scope = "Embarque de Combustible según Litoral"
            else:
                sub_context = "GENERAL"
                scope = "Combustible Marino General"
                
        # Ro-Ro / Vehicles
        elif "veh" in text or "car" in text or "auto" in text:
            domain = "CARGA_RODANTE_RORO"
            sub_context = "VEHICULOS_POR_PUERTO"
            unit = "UNIDADES"
            scope = "Movimiento de Vehículos (Desembarque y Embarque)"
            
        # General Port Macro Indicators
        elif "indicador" in text:
            domain = "INDICADORES_MACRO_PORTUARIOS"
            sub_context = "SISTEMA_PORTUARIO_NACIONAL"
            unit = "MULTI_METRICA"
            scope = "Consolidado Portuario (Carga TM, Cruceros, Cabotaje)"
            
        # Public Vessel Registry
        elif "registro" in text or "nave" in text or "propiedad" in text or "tramite" in text:
            domain = "REGISTRO_NAVAL_PANAMA"
            sub_context = "TITULOS_E_HIPOTECAS"
            unit = "TRAMITES_Y_DOCUMENTOS"
            scope = "Trámites Registrales de Naves y Certificados"
            
        # Seafarers / Maritime Labor
        elif "gente de mar" in text or "titulaci" in text:
            domain = "GENTE_DE_MAR"
            sub_context = "TITULACION_Y_CERTIFICACION"
            unit = "LICENCIAS_Y_CARNETS"
            scope = "Titulaciones Marítimas STCW"
            
        else:
            domain = "OTROS"
            sub_context = "ADMINISTRATIVO"
            unit = "VARIOS"
            scope = "Otros Documentos Institucionales"
            
        return {
            "domain": domain,
            "sub_context": sub_context,
            "unit": unit,
            "scope": scope
        }

    @staticmethod
    def classify_structure(columns: List[str]) -> str:
        """
        Determines the tabular orientation and structural pattern.
        """
        cols_lower = [c.lower() for c in columns]
        # Check if months are in column headers (wide format e.g. ene-21, feb-21)
        month_col_patterns = [r'(ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)[-_]\d{2}',
                              r'\d{2}[-_](ene|feb|mar|abr|may|jun|jul|ago|sep|oct|nov|dic)']
        has_month_columns = any(
            any(re.search(p, c) for p in month_col_patterns) for c in cols_lower
        )
        if has_month_columns:
            return "HORIZONTAL_WIDE_MONTHS_AS_COLUMNS"
            
        # Check if year and month are rows and ports are columns
        has_year = any("a" in c and "o" in c for c in cols_lower)
        has_month = any("mes" in c for c in cols_lower)
        if has_year and has_month:
            return "VERTICAL_WIDE_PORTS_AS_COLUMNS"
            
        return "GENERIC_TABULAR"

    def run_classification(self) -> pd.DataFrame:
        """
        Executes classification across all 353 files in raw directory.
        """
        logger.info(f"Starting classification of raw datasets in {self.raw_dir}")
        records = []
        
        all_files = glob.glob(str(self.raw_dir / "*.csv"))
        logger.info(f"Found {len(all_files)} files to inspect.")
        
        for filepath_str in all_files:
            filepath = Path(filepath_str)
            filename = filepath.name
            size_bytes = filepath.stat().st_size
            
            enc, delim = self.detect_encoding_and_delimiter(filepath)
            
            # Read header and sample
            cols = []
            row_count = 0
            try:
                df_sample = pd.read_csv(filepath, sep=delim, encoding=enc, nrows=5, on_bad_lines="skip")
                cols = [c.strip() for c in df_sample.columns.tolist()]
                # Approximate row count
                with open(filepath, "r", encoding=enc, errors="replace") as f:
                    row_count = sum(1 for _ in f) - 1
            except Exception as e:
                logger.warning(f"Error reading {filename}: {e}")
                
            # Lookup in catalog if available
            title = filename
            slug = filename
            if not self.catalog_df.empty:
                match = self.catalog_df[self.catalog_df["local_file"] == filename]
                if not match.empty:
                    title = match.iloc[0]["title"]
                    slug = match.iloc[0]["slug"]
                    
            context_info = self.classify_context(title, slug)
            structure_type = self.classify_structure(cols)
            
            # Detect Year and Month coverage from columns or data
            record = {
                "filename": filename,
                "title": title,
                "domain": context_info["domain"],
                "sub_context": context_info["sub_context"],
                "unit": context_info["unit"],
                "scope": context_info["scope"],
                "structure_type": structure_type,
                "encoding": enc,
                "delimiter": delim,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2),
                "row_count": row_count,
                "column_count": len(cols),
                "columns": cols
            }
            records.append(record)
            
        df_classified = pd.DataFrame(records)
        
        # Save output artifacts
        output_csv = METADATA_DIR / "classified_datasets.csv"
        output_json = METADATA_DIR / "classified_datasets.json"
        df_classified.to_csv(output_csv, index=False, encoding="utf-8-sig")
        
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
            
        logger.info(f"Classification finished. Results saved to {output_csv} and {output_json}")
        self.generate_markdown_summary(df_classified)
        return df_classified

    def generate_markdown_summary(self, df: pd.DataFrame):
        """Generates a structured Markdown taxonomy report."""
        REPORTS_DIR.mkdir(exist_ok=True)
        report_path = REPORTS_DIR / "DATASET_TAXONOMY_REPORT.md"
        
        domain_counts = df["domain"].value_counts()
        structure_counts = df["structure_type"].value_counts()
        encoding_counts = df["encoding"].value_counts()
        delimiter_counts = df["delimiter"].value_counts()
        
        content = f"""# Reporte de Taxonomía y Clasificación Exhaustiva de Datasets AMP

## 1. Visión General
Se han inspeccionado y clasificado algorítmicamente un total de **{len(df)} datasets** obtenidos de la Autoridad Marítima de Panamá.

### Métricas de Distribución por Dominio Operativo
| Dominio de Negocio | Cantidad de Datasets | % del Total |
| :--- | :--- | :--- |
"""
        for domain, count in domain_counts.items():
            pct = (count / len(df)) * 100
            content += f"| `{domain}` | {count} | {pct:.1f}% |\n"
            
        content += f"""
### Distribución por Estructura y Orientación Tabular
| Tipo de Estructura | Cantidad | Descripción |
| :--- | :--- | :--- |
"""
        for struct, count in structure_counts.items():
            desc = "Meses en columnas (requiere unpivot/melt)" if "HORIZONTAL" in struct else "Puertos en columnas y meses en filas"
            content += f"| `{struct}` | {count} | {desc} |\n"
            
        content += f"""
### Calidad Técnica: Encodings y Delimitadores
- **Encodings:** {encoding_counts.to_dict()}
- **Delimitadores:** {delimiter_counts.to_dict()}

## 2. Detalle Exhaustivo por Dominio Operativo

"""
        for domain, group in df.groupby("domain"):
            content += f"### Dominio: `{domain}` ({len(group)} datasets)\n\n"
            content += f"- **Unidad de Medida Principal:** {group['unit'].iloc[0]}\n"
            content += f"- **Sub-contextos identificados:** {group['sub_context'].unique().tolist()}\n"
            content += f"- **Tamaño total:** {group['size_kb'].sum():.2f} KB\n\n"
            content += "| Archivo Ejemplo | Alcance Operativo | Filas | Columnas |\n| :--- | :--- | :--- | :--- |\n"
            for _, row in group.head(5).iterrows():
                content += f"| `{row['filename'][:45]}` | {row['scope']} | {row['row_count']} | {row['column_count']} |\n"
            content += "\n---\n\n"
            
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Taxonomy report written to {report_path}")

if __name__ == "__main__":
    classifier = DatasetClassifier()
    df_result = classifier.run_classification()
    print("Classification summary:")
    print(df_result["domain"].value_counts())
