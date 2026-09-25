"""
Data Normalization and Silver Layer Transformation Engine.
Adheres to MLOps Masterclass Section 1.3, 11 & 12:
- Medallion Architecture (Bronze -> Silver Parquet)
- Resilient polymorphic parsing (Encoding & Delimiter detection)
- Bitemporal snapshot deduplication
- Schema harmonization & Canonical entity mapping
- Unpivoting (Melt) to Tidy Data structures
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from src.utils.logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
SILVER_DIR = PROJECT_ROOT / "data" / "silver"
METADATA_DIR = PROJECT_ROOT / "data" / "metadata"
SILVER_DIR.mkdir(exist_ok=True, parents=True)

SPANISH_MONTHS = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
    "ene": 1, "feb": 2, "mar": 3, "abr": 4, "may": 5, "jun": 6,
    "jul": 7, "ago": 8, "sep": 9, "set": 9, "oct": 10, "nov": 11, "dic": 12
}

CANONICAL_PORTS = {
    "bocas fruit": ("Bocas Fruit Co.", "Atlántico"),
    "cct": ("Colon Container Terminal", "Atlántico"),
    "colon container": ("Colon Container Terminal", "Atlántico"),
    "mit": ("SSA Marine MIT", "Atlántico"),
    "manzanillo": ("SSA Marine MIT", "Atlántico"),
    "ssa marine": ("SSA Marine MIT", "Atlántico"),
    "balboa": ("Puerto Balboa", "Pacífico"),
    "cristobal": ("Puerto Cristóbal", "Atlántico"),
    "cristóbal": ("Puerto Cristóbal", "Atlántico"),
    "psa": ("PSA Panama International Terminal", "Pacífico")
}

def is_year_col(col_name: str) -> bool:
    """Strictly checks if a column represents Year/Año without matching other words like Bocas."""
    c = str(col_name).strip().lower()
    return c in ['año', 'a\xf1o', 'ao', 'ano', 'year', 'años', 'a\xf1os', 'anos'] or c.startswith(('año ', 'a\xf1o ', 'ao ', 'ano '))

def is_month_col(col_name: str) -> bool:
    """Strictly checks if a column represents Month/Mes."""
    c = str(col_name).strip().lower()
    return c in ['mes', 'month', 'meses'] or c.startswith(('mes ', 'month '))

def clean_year(val: Any) -> Optional[int]:
    """Extracts integer 4-digit year from strings like '2026(p)' or '2021(P)'."""
    if pd.isna(val):
        return None
    val_str = str(val).strip()
    match = re.search(r'\b(20\d\d|19\d\d)\b', val_str)
    if match:
        yr = int(match.group(1))
        if 2010 <= yr <= 2026:
            return yr
    return None

def clean_month(val: Any) -> Optional[int]:
    """Converts month name to integer (1-12)."""
    if pd.isna(val):
        return None
    val_str = str(val).strip().lower()
    for m_name, m_num in SPANISH_MONTHS.items():
        if m_name in val_str:
            return m_num
    if val_str.isdigit():
        num = int(val_str)
        if 1 <= num <= 12:
            return num
    return None

def clean_numeric(val: Any, allow_negative: bool = False) -> Optional[float]:
    """Cleans numeric values handling commas, whitespace, and null tokens."""
    if pd.isna(val):
        return None
    val_str = str(val).strip().replace(',', '').replace(' ', '')
    if val_str in ['', '-', 'nd', 'n/d', 'null', 'nan']:
        return None
    try:
        f_val = float(val_str)
        if not allow_negative and f_val < 0:
            # Accounting adjustment in raw port data: clip to 0.0 for physical volume
            return 0.0
        return f_val
    except ValueError:
        return None

def detect_port_and_litoral(col_name: str) -> Tuple[Optional[str], Optional[str]]:
    col_lower = col_name.lower()
    for alias, (canonical_name, littoral) in CANONICAL_PORTS.items():
        if alias in col_lower:
            return canonical_name, littoral
    return None, None

class SilverNormalizer:
    """
    Transforms raw CSV files into consolidated, deduplicated Silver Parquet tables.
    """

    def __init__(self, raw_dir: Path = RAW_DIR, silver_dir: Path = SILVER_DIR):
        self.raw_dir = raw_dir
        self.silver_dir = silver_dir
        
    def read_csv_robust(self, filepath: Path) -> Optional[pd.DataFrame]:
        with open(filepath, "rb") as f:
            raw = f.read(4096)
        enc = "utf-8"
        try:
            raw.decode("utf-8")
        except UnicodeDecodeError:
            enc = "latin-1"
        sample = raw.decode(enc, errors="replace")
        first_line = sample.splitlines()[0] if sample.splitlines() else ""
        delim = ";" if ";" in first_line else ","
        try:
            df = pd.read_csv(filepath, sep=delim, encoding=enc, on_bad_lines="skip")
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception as e:
            logger.warning(f"Failed to read {filepath.name}: {e}")
            return None

    def normalize_containers(self) -> pd.DataFrame:
        """
        Consolidates all container datasets (Total, Destino, Tipo) into fact_containers.
        """
        logger.info("Normalizing Container Datasets...")
        all_files = glob.glob(str(self.raw_dir / "*.csv"))
        container_files = [f for f in all_files if "contenedor" in Path(f).name.lower()]
        
        records = []
        for file_path_str in container_files:
            file_path = Path(file_path_str)
            filename = file_path.name.lower()
            df = self.read_csv_robust(file_path)
            if df is None or df.empty:
                continue
                
            # Identify unit
            unit = "TEU" if "teu" in filename else "UNIDADES"
            
            # Identify sub-category
            if "destino" in filename:
                dataset_cat = "DESTINO"
            elif "tipo" in filename:
                dataset_cat = "TIPO"
            else:
                dataset_cat = "TOTAL"
                
            # Find year and month columns strictly
            year_col = next((c for c in df.columns if is_year_col(c)), None)
            month_col = next((c for c in df.columns if is_month_col(c)), None)
            
            if not year_col or not month_col:
                continue
                
            for _, row in df.iterrows():
                yr = clean_year(row[year_col])
                mo = clean_month(row[month_col])
                if not yr or not mo:
                    continue
                    
                for col in df.columns:
                    if col in [year_col, month_col] or "unnamed" in col.lower():
                        continue
                    port_name, littoral = detect_port_and_litoral(col)
                    if not port_name:
                        continue
                        
                    col_lower = col.lower()
                    sub_cat = "TOTAL"
                    if dataset_cat == "DESTINO":
                        if "trasbordo" in col_lower:
                            sub_cat = "TRASBORDO"
                        elif "local" in col_lower:
                            sub_cat = "LOCAL"
                        elif "zona libre" in col_lower or "zl" in col_lower:
                            sub_cat = "ZONA_LIBRE"
                    elif dataset_cat == "TIPO":
                        if "lleno" in col_lower:
                            sub_cat = "LLENOS"
                        elif "vaco" in col_lower or "vacío" in col_lower:
                            sub_cat = "VACIOS"
                            
                    val = clean_numeric(row[col])
                    if val is not None:
                        records.append({
                            "year": yr,
                            "month": mo,
                            "port": port_name,
                            "littoral": littoral,
                            "category": dataset_cat,
                            "sub_category": sub_cat,
                            "metric_unit": unit,
                            "value": val,
                            "source_file": file_path.name
                        })
                        
        df_out = pd.DataFrame(records)
        if df_out.empty:
            logger.error("No container records were extracted!")
            return df_out
            
        # Deduplication strategy: Snapshot resolution
        # Group by (year, month, port, category, sub_category, metric_unit) and take last or max observation
        # Since files were published chronologically, later files contain final revisions
        df_out = df_out.sort_values(by=["source_file"])
        df_dedup = df_out.drop_duplicates(
            subset=["year", "month", "port", "category", "sub_category", "metric_unit"],
            keep="last"
        ).copy()
        
        # Build standard datetime timestamp
        df_dedup["date"] = pd.to_datetime(
            df_dedup["year"].astype(str) + "-" + df_dedup["month"].astype(str).str.zfill(2) + "-01"
        )
        df_dedup = df_dedup.sort_values(by=["date", "port", "category", "sub_category"]).reset_index(drop=True)
        
        # Save Parquet
        out_parquet = self.silver_dir / "fact_containers.parquet"
        df_dedup.to_parquet(out_parquet, index=False, compression="snappy")
        logger.info(f"Container Silver table persisted: {len(df_dedup)} rows -> {out_parquet}")
        return df_dedup

    def normalize_bunkering(self) -> pd.DataFrame:
        """
        Consolidates bunkering (marine fuel) sales and barge operations.
        """
        logger.info("Normalizing Bunkering Datasets...")
        all_files = glob.glob(str(self.raw_dir / "*.csv"))
        bunkering_files = [f for f in all_files if "combustible" in Path(f).name.lower() or "barcaza" in Path(f).name.lower()]
        
        records = []
        for file_path_str in bunkering_files:
            file_path = Path(file_path_str)
            filename = file_path.name.lower()
            df = self.read_csv_robust(file_path)
            if df is None or df.empty:
                continue
                
            year_col = next((c for c in df.columns if is_year_col(c)), None)
            month_col = next((c for c in df.columns if is_month_col(c)), None)
            
            # Format 1: Vertical tables (Año, Mes, Naves Pacífico, VLSFO Pacífico, ...)
            if year_col and month_col:
                for _, row in df.iterrows():
                    yr = clean_year(row[year_col])
                    mo = clean_month(row[month_col])
                    if not yr or not mo:
                        continue
                        
                    for col in df.columns:
                        if col in [year_col, month_col] or "unnamed" in col.lower():
                            continue
                        col_l = col.lower()
                        littoral = "Pacífico" if "pac" in col_l else ("Atlántico" if "atl" in col_l else "Nacional")
                        
                        # Detect product / metric
                        product = "GENERAL"
                        unit = "TM"
                        if "naves" in col_l:
                            product = "NAVES_ATENDIDAS"
                            unit = "UNIDADES"
                        elif "barcazas" in col_l:
                            product = "BARCAZAS_OPERANDO"
                            unit = "UNIDADES"
                        elif "vlsfo" in col_l:
                            product = "VLSFO"
                        elif "rmg" in col_l:
                            product = "RMG_380"
                        elif "lsmgo" in col_l:
                            product = "LSMGO"
                        elif "mgo" in col_l:
                            product = "MGO"
                        elif "bio" in col_l:
                            product = "BIO_COMBUSTIBLE"
                        elif "fuel oil" in col_l:
                            product = "FUEL_OIL"
                            unit = "BARRILES" if "barril" in col_l else "TM"
                        elif "diesel" in col_l:
                            product = "DIESEL_MARINO"
                            unit = "BARRILES" if "barril" in col_l else "TM"
                            
                        val = clean_numeric(row[col])
                        if val is not None:
                            records.append({
                                "year": yr,
                                "month": mo,
                                "littoral": littoral,
                                "product": product,
                                "metric_unit": unit,
                                "value": val,
                                "source_file": file_path.name
                            })
                            
            # Format 2: Horizontal wide tables with months as columns (ene-21, feb-21)
            else:
                prod_col = next((c for c in df.columns if any(k in c.lower() for k in ["producto", "combustible", "venta"])), None)
                lit_col = next((c for c in df.columns if "litoral" in c.lower() or "área" in c.lower() or "area" in c.lower()), None)
                if not prod_col:
                    continue
                    
                # Extract year from filename (e.g. 2021)
                yr_match = re.search(r'(20\d\d)', filename)
                default_year = int(yr_match.group(1)) if yr_match else 2021
                
                for _, row in df.iterrows():
                    prod_val = str(row[prod_col]).strip()
                    lit_val = str(row[lit_col]).strip() if lit_col else "Nacional"
                    littoral = "Pacífico" if "pac" in lit_val.lower() else ("Atlántico" if "atl" in lit_val.lower() else "Nacional")
                    
                    product = "FUEL_OIL" if "fuel" in prod_val.lower() else ("DIESEL_MARINO" if "diesel" in prod_val.lower() else "GENERAL")
                    unit = "BARRILES" if "barril" in prod_val.lower() else "TM"
                    
                    for col in df.columns:
                        if col in [prod_col, lit_col] or "unnamed" in col.lower() or "total" in col.lower():
                            continue
                        # Try parsing month and year from col name e.g. ene-21 or 21-ene
                        m_num = None
                        yr = default_year
                        for m_name, num in SPANISH_MONTHS.items():
                            if m_name in col.lower():
                                m_num = num
                                break
                        m_yr = re.search(r'(\d{2})', col)
                        if m_yr:
                            yr_suffix = int(m_yr.group(1))
                            yr = 2000 + yr_suffix if yr_suffix < 50 else 1900 + yr_suffix
                            
                        if m_num:
                            val = clean_numeric(row[col])
                            if val is not None:
                                records.append({
                                    "year": yr,
                                    "month": m_num,
                                    "littoral": littoral,
                                    "product": product,
                                    "metric_unit": unit,
                                    "value": val,
                                    "source_file": file_path.name
                                })
                                
        df_out = pd.DataFrame(records)
        if df_out.empty:
            logger.error("No bunkering records were extracted!")
            return df_out
            
        df_out = df_out.sort_values(by=["source_file"])
        df_dedup = df_out.drop_duplicates(
            subset=["year", "month", "littoral", "product", "metric_unit"],
            keep="last"
        ).copy()
        
        df_dedup["date"] = pd.to_datetime(
            df_dedup["year"].astype(str) + "-" + df_dedup["month"].astype(str).str.zfill(2) + "-01"
        )
        df_dedup = df_dedup.sort_values(by=["date", "littoral", "product"]).reset_index(drop=True)
        
        out_parquet = self.silver_dir / "fact_bunkering.parquet"
        df_dedup.to_parquet(out_parquet, index=False, compression="snappy")
        logger.info(f"Bunkering Silver table persisted: {len(df_dedup)} rows -> {out_parquet}")
        return df_dedup

    def normalize_roro(self) -> pd.DataFrame:
        """
        Consolidates Ro-Ro vehicle movements across ports.
        """
        logger.info("Normalizing Ro-Ro Vehicle Datasets...")
        all_files = glob.glob(str(self.raw_dir / "*.csv"))
        roro_files = [f for f in all_files if "vehiculo" in Path(f).name.lower()]
        
        records = []
        for file_path_str in roro_files:
            file_path = Path(file_path_str)
            df = self.read_csv_robust(file_path)
            if df is None or df.empty:
                continue
                
            year_col = next((c for c in df.columns if is_year_col(c)), None)
            month_col = next((c for c in df.columns if is_month_col(c)), None)
            
            if not year_col or not month_col:
                continue
                
            for _, row in df.iterrows():
                yr = clean_year(row[year_col])
                mo = clean_month(row[month_col])
                if not yr or not mo:
                    continue
                    
                for col in df.columns:
                    if col in [year_col, month_col] or "unnamed" in col.lower():
                        continue
                    port_name, littoral = detect_port_and_litoral(col)
                    if not port_name:
                        continue
                        
                    col_l = col.lower()
                    op = "TOTAL"
                    if "desembarque" in col_l:
                        op = "DESEMBARQUE_TRASBORDO" if "trasbordo" in col_l else "DESEMBARQUE_LOCAL"
                    elif "embarque" in col_l:
                        op = "EMBARQUE_TRASBORDO" if "trasbordo" in col_l else "EMBARQUE_LOCAL"
                        
                    val = clean_numeric(row[col])
                    if val is not None:
                        records.append({
                            "year": yr,
                            "month": mo,
                            "port": port_name,
                            "littoral": littoral,
                            "operation": op,
                            "metric_unit": "UNIDADES_VEHICULOS",
                            "value": val,
                            "source_file": file_path.name
                        })
                        
        df_out = pd.DataFrame(records)
        if df_out.empty:
            logger.error("No Ro-Ro records extracted!")
            return df_out
            
        df_out = df_out.sort_values(by=["source_file"])
        df_dedup = df_out.drop_duplicates(
            subset=["year", "month", "port", "operation"],
            keep="last"
        ).copy()
        
        df_dedup["date"] = pd.to_datetime(
            df_dedup["year"].astype(str) + "-" + df_dedup["month"].astype(str).str.zfill(2) + "-01"
        )
        df_dedup = df_dedup.sort_values(by=["date", "port", "operation"]).reset_index(drop=True)
        
        out_parquet = self.silver_dir / "fact_roro.parquet"
        df_dedup.to_parquet(out_parquet, index=False, compression="snappy")
        logger.info(f"Ro-Ro Silver table persisted: {len(df_dedup)} rows -> {out_parquet}")
        return df_dedup

    def normalize_macro(self) -> pd.DataFrame:
        """
        Consolidates macro port indicators (Total Cargo TM, Cruises, Cabotage, etc.).
        """
        logger.info("Normalizing Macro Indicators Datasets...")
        all_files = glob.glob(str(self.raw_dir / "*.csv"))
        macro_files = [f for f in all_files if "indicador-maritimo-portuario" in Path(f).name.lower()]
        
        records = []
        for file_path_str in macro_files:
            file_path = Path(file_path_str)
            df = self.read_csv_robust(file_path)
            if df is None or df.empty:
                continue
                
            year_col = next((c for c in df.columns if is_year_col(c)), None)
            month_col = next((c for c in df.columns if is_month_col(c)), None)
            
            if not year_col or not month_col:
                continue
                
            for _, row in df.iterrows():
                yr = clean_year(row[year_col])
                mo = clean_month(row[month_col])
                if not yr or not mo:
                    continue
                    
                for col in df.columns:
                    if col in [year_col, month_col] or "unnamed" in col.lower():
                        continue
                    col_l = col.lower()
                    metric_name = "OTRO"
                    unit = "VALOR"
                    if "teu" in col_l:
                        metric_name = "CONTENEDORES_TOTAL_TEU"
                        unit = "TEU"
                    elif "unidades" in col_l or "ontenedor" in col_l:
                        metric_name = "CONTENEDORES_TOTAL_UNIDADES"
                        unit = "UNIDADES"
                    elif "vehic" in col_l:
                        metric_name = "VEHICULOS_TOTAL"
                        unit = "UNIDADES"
                    elif "tonelada" in col_l or "carga" in col_l:
                        metric_name = "CARGA_TOTAL_TM"
                        unit = "TONELADAS_METRICAS"
                    elif "crucero" in col_l:
                        metric_name = "PASAJEROS_CRUCERO"
                        unit = "PASAJEROS"
                    elif "dom" in col_l or "nacional" in col_l:
                        metric_name = "PASAJEROS_CABOTAJE"
                        unit = "PASAJEROS"
                    elif "oficial" in col_l:
                        metric_name = "LICENCIAS_OFICIALES"
                        unit = "DOCUMENTOS"
                    elif "marino" in col_l:
                        metric_name = "CARNETS_MARINOS"
                        unit = "DOCUMENTOS"
                        
                    val = clean_numeric(row[col])
                    if val is not None:
                        records.append({
                            "year": yr,
                            "month": mo,
                            "metric_name": metric_name,
                            "metric_unit": unit,
                            "value": val,
                            "source_file": file_path.name
                        })
                        
        df_out = pd.DataFrame(records)
        if df_out.empty:
            logger.error("No macro indicator records extracted!")
            return df_out
            
        df_out = df_out.sort_values(by=["source_file"])
        df_dedup = df_out.drop_duplicates(
            subset=["year", "month", "metric_name"],
            keep="last"
        ).copy()
        
        df_dedup["date"] = pd.to_datetime(
            df_dedup["year"].astype(str) + "-" + df_dedup["month"].astype(str).str.zfill(2) + "-01"
        )
        df_dedup = df_dedup.sort_values(by=["date", "metric_name"]).reset_index(drop=True)
        
        out_parquet = self.silver_dir / "fact_port_macro.parquet"
        df_dedup.to_parquet(out_parquet, index=False, compression="snappy")
        logger.info(f"Macro Silver table persisted: {len(df_dedup)} rows -> {out_parquet}")
        return df_dedup

    def run_all(self):
        logger.info("=== Running Complete Silver Layer Normalization ===")
        df_c = self.normalize_containers()
        df_b = self.normalize_bunkering()
        df_r = self.normalize_roro()
        df_m = self.normalize_macro()
        logger.info("=== All Silver tables normalized and persisted successfully ===")

if __name__ == "__main__":
    normalizer = SilverNormalizer()
    normalizer.run_all()
