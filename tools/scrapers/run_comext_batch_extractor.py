#!/usr/bin/env python3
"""
=============================================================================
ORQUESTADOR INDUSTRIAL DE EXTRACCIÓN Y UNIFICACIÓN DE COMERCIO EXTERIOR (INEC)
Autor: Ing. Miguel Antonio Benítez González (UTP) - GNU GPL-3.0
=============================================================================
Orquesta de forma automatizada y resiliente la descarga y unificación analítica
de datasets de Importaciones y Exportaciones del INEC Panamá.
- Identifica capítulos faltantes de forma dinámica.
- Garantiza checkpointing estricto evitando re-descargas.
- Aplica nombres normalizados estándar y consolida a Parquet Snappy.
=============================================================================
"""
import os
import sys
import glob
import json
import argparse
import asyncio
import logging
from typing import List, Dict, Set, Tuple

# Rutas estándar de los repositorios de datos
IMPORTS_DIR = r"C:\Users\mbeni\Downloads\datasets_imports"
EXPORTS_DIR = r"C:\Users\mbeni\Downloads\datasets_exports"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)
logger = logging.getLogger("ComextOrchestrator")


def audit_datasets() -> Dict[str, any]:
    """Audita la cobertura de datos crudos y procesados en importaciones y exportaciones."""
    report = {"imports": {}, "exports": {}}

    # 1. Imports
    imp_raw = os.path.join(IMPORTS_DIR, "data", "raw")
    imp_proc = os.path.join(IMPORTS_DIR, "data", "processed")
    if os.path.exists(imp_raw):
        for cat in sorted(os.listdir(imp_raw)):
            cat_p = os.path.join(imp_raw, cat)
            if os.path.isdir(cat_p):
                files = glob.glob(os.path.join(cat_p, "**", "*_raw.*"), recursive=True)
                caps = set()
                for f in files:
                    for part in f.replace("\\", "/").split("/"):
                        if part.startswith("capitulo-"):
                            caps.add(part.split("-")[1])
                report["imports"][cat] = {
                    "total_files": len(files),
                    "chapters_count": len(caps),
                    "chapters": sorted(list(caps))
                }

    # 2. Exports
    exp_raw = os.path.join(EXPORTS_DIR, "data", "raw")
    exp_proc = os.path.join(EXPORTS_DIR, "data", "processed")
    if os.path.exists(exp_raw):
        for cat in sorted(os.listdir(exp_raw)):
            cat_p = os.path.join(exp_raw, cat)
            if os.path.isdir(cat_p):
                files = glob.glob(os.path.join(cat_p, "**", "*_raw.*"), recursive=True)
                caps = set()
                for f in files:
                    for part in f.replace("\\", "/").split("/"):
                        if part.startswith("capitulo-"):
                            caps.add(part.split("-")[1])
                report["exports"][cat] = {
                    "total_files": len(files),
                    "chapters_count": len(caps),
                    "chapters": sorted(list(caps))
                }

    return report


def get_missing_chapters(target: str, report_id: int) -> List[str]:
    """Identifica la lista de capítulos con 0 archivos en disco."""
    missing = []
    if target == "imports":
        base = os.path.join(IMPORTS_DIR, "data", "raw")
        folder = "03_valor_importacion_por_inciso_y_pais_origen" if report_id == 3 else "04_peso_valor_importacion_por_anio_inciso_y_pais"
        cat_p = os.path.join(base, folder)
        if os.path.exists(cat_p):
            for d in sorted(os.listdir(cat_p)):
                dp = os.path.join(cat_p, d)
                if os.path.isdir(dp) and d.startswith("capitulo-"):
                    files = [f for f in os.listdir(dp) if not f.startswith(".")]
                    if len(files) == 0:
                        cap_code = d.split("-")[1]
                        missing.append(cap_code)
    elif target == "exports":
        base = os.path.join(EXPORTS_DIR, "data", "raw")
        folder = "03_valor_exportacion_por_inciso_y_pais_destino" if report_id == 3 else "04_peso_valor_exportacion_por_anio_inciso_y_pais"
        cat_p = os.path.join(base, folder)
        if os.path.exists(cat_p):
            for d in sorted(os.listdir(cat_p)):
                dp = os.path.join(cat_p, d)
                if os.path.isdir(dp) and d.startswith("capitulo-"):
                    files = [f for f in os.listdir(dp) if not f.startswith(".")]
                    if len(files) == 0:
                        cap_code = d.split("-")[1]
                        missing.append(cap_code)
    return missing


async def run_extraction(target: str, report_id: int, chapters: List[str], max_slices: int = None, render_delay: int = 8):
    """Ejecuta el scraper correspondiente para una lista de capítulos."""
    if target == "imports":
        sys.path.insert(0, IMPORTS_DIR)
        from src.scraper.core.inec_scraper import INECMasterScraper
        scraper = INECMasterScraper(
            os.path.join(IMPORTS_DIR, "data", "raw"),
            os.path.join(IMPORTS_DIR, "data", "processed")
        )
        logger.info(f"[Imports R{report_id}] Procesando {len(chapters)} capítulos: {chapters}")
        await scraper.scrape_report(
            report_id,
            filter_capitulos=chapters,
            max_slices_per_level=max_slices,
            render_delay=render_delay
        )
    elif target == "exports":
        sys.path.insert(0, EXPORTS_DIR)
        from src.scraper.core.inec_export_scraper import INECExportMasterScraper
        scraper = INECExportMasterScraper(
            os.path.join(EXPORTS_DIR, "data", "raw"),
            os.path.join(EXPORTS_DIR, "data", "processed")
        )
        logger.info(f"[Exports R{report_id}] Procesando {len(chapters)} capítulos: {chapters}")
        await scraper.scrape_report(
            report_id,
            filter_capitulos=chapters,
            max_slices_per_level=max_slices,
            render_delay=render_delay
        )


def run_unification(target: str):
    """Ejecuta la consolidación a Parquet para el repositorio seleccionado."""
    if target in ["imports", "both"]:
        logger.info("=== Consolidando Importaciones a Parquet ===")
        sys.path.insert(0, IMPORTS_DIR)
        from src.processing.transformers import DatasetUnifier as ImpUnifier
        u = ImpUnifier(
            os.path.join(IMPORTS_DIR, "data", "raw"),
            os.path.join(IMPORTS_DIR, "data", "processed")
        )
        res = u.unify_all_categories()
        logger.info(f"Importaciones unificadas: {len(res)} categorías guardadas en Parquet.")

    if target in ["exports", "both"]:
        logger.info("=== Consolidando Exportaciones a Parquet ===")
        sys.path.insert(0, EXPORTS_DIR)
        from src.processing.transformers import DatasetUnifier as ExpUnifier
        u = ExpUnifier(
            os.path.join(EXPORTS_DIR, "data", "raw"),
            os.path.join(EXPORTS_DIR, "data", "processed")
        )
        res = u.unify_all_categories()
        logger.info(f"Exportaciones unificadas: {len(res)} categorías guardadas en Parquet.")


def main():
    parser = argparse.ArgumentParser(description="Orquestador Maestro de Comercio Exterior INEC Panamá")
    parser.add_argument("--action", choices=["audit", "extract", "unify", "all"], default="audit",
                        help="Acción a ejecutar: audit (diagnóstico), extract (descarga), unify (consolidar a parquet), all")
    parser.add_argument("--target", choices=["imports", "exports", "both"], default="imports",
                        help="Objetivo de datos: imports, exports, both")
    parser.add_argument("--reports", type=str, default="3",
                        help="Reportes a procesar separados por coma (ej. '3' o '3,4')")
    parser.add_argument("--capitulos", type=str, default="missing",
                        help="'missing' para todos los capítulos pendientes, o lista separada por comas (ej. '15,16,17')")
    parser.add_argument("--batch-size", type=int, default=5,
                        help="Cantidad de capítulos por lote (por defecto: 5)")
    parser.add_argument("--max-slices", type=int, default=None,
                        help="Límite opcional de slices para pruebas")
    parser.add_argument("--render-delay", type=int, default=10,
                        help="Delay de renderizado SSRS en segundos")
    args = parser.parse_args()

    if args.action in ["audit", "all"]:
        logger.info("=== DIAGNÓSTICO DE COBERTURA DE DATASETS COMEXT ===")
        aud = audit_datasets()
        print("\n--- IMPORTACIONES ---")
        for cat, info in aud["imports"].items():
            print(f"  {cat[:50]:<50} | {info['total_files']:>5} archivos | {info['chapters_count']:>2} capítulos")
        print("\n--- EXPORTACIONES ---")
        for cat, info in aud["exports"].items():
            print(f"  {cat[:50]:<50} | {info['total_files']:>5} archivos | {info['chapters_count']:>2} capítulos")
        print("-" * 75)

    if args.action in ["extract", "all"]:
        rep_ids = [int(r.strip()) for r in args.reports.split(",") if r.strip().isdigit()]
        targets = ["imports", "exports"] if args.target == "both" else [args.target]

        for t in targets:
            for rid in rep_ids:
                if args.capitulos == "missing":
                    chaps = get_missing_chapters(t, rid)
                else:
                    chaps = [c.strip().zfill(2) for c in args.capitulos.split(",")]

                if not chaps:
                    logger.info(f"[{t.upper()} R{rid}] No hay capítulos faltantes. 100% al día.")
                    continue

                logger.info(f"[{t.upper()} R{rid}] Capítulos faltantes identificados: {len(chaps)} -> {chaps[:10]}...")
                batch = chaps[:args.batch_size]
                logger.info(f"[{t.upper()} R{rid}] Procesando lote de {len(batch)} capítulos: {batch}")
                
                asyncio.run(
                    run_extraction(
                        t, rid, batch,
                        max_slices=args.max_slices,
                        render_delay=args.render_delay
                    )
                )

    if args.action in ["unify", "all"]:
        run_unification(args.target)


if __name__ == "__main__":
    main()
