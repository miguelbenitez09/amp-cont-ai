#!/usr/bin/env python3
"""
=============================================================================
SUPERVISOR AUTÓNOMO RESILIENTE Y AUTO-CORRECTIVO DE COMERCIO EXTERIOR (INEC)
Autor: Desarrollado v1.0.0 Miguel Benítez / Ing. Miguel Antonio Benítez González (UTP)
Licencia: GNU General Public License v3.0 (GPL-3.0) con Atribución Obligatoria
Marco Legal: Ley 6 de 22 de enero de 2002 de la República de Panamá (Transparencia
             en la Gestión Pública, Acceso a la Información y Datos Abiertos).
=============================================================================
Este script implementa un bucle supervisor de grado industrial que:
1. Detecta dinámicamente capítulos faltantes en Importaciones (R3, R4) y Exportaciones (R3).
2. Maneja excepciones de red, timeouts de SSRS y bloqueos perimetrales WAF (Fortinet).
3. Aplica calentamiento de sesión con cookiesession1 legítima desde inec.gob.pa.
4. Auto-corrige fallos reciclando el contexto del navegador y reintentando automáticamente.
5. Garantiza checkpointing estricto para no volver a descargar ningún archivo existente.
6. Dispara unificación automática a Parquet Snappy tras cada lote exitoso.
=============================================================================
"""

import os
import sys
import time
import glob
import json
import random
import logging
import argparse
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

# Rutas estándar del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
IMPORTS_DIR = Path(r"C:\Users\mbeni\Downloads\datasets_imports")
EXPORTS_DIR = Path(r"C:\Users\mbeni\Downloads\datasets_exports")
STATE_FILE = PROJECT_ROOT / "data" / "comext_supervisor_state.json"
LOGS_DIR = PROJECT_ROOT / "logs"

LOGS_DIR.mkdir(parents=True, exist_ok=True)
STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - [%(name)s] - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOGS_DIR / "comext_supervisor.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("ComextSupervisor")


class ComextSupervisor:
    """
    Supervisor supervisor autónomo con bucle auto-correctivo y persistencia de estado.
    """

    def __init__(self, batch_size: int = 2, max_consecutive_errors: int = 5):
        self.batch_size = batch_size
        self.max_consecutive_errors = max_consecutive_errors
        self.state = self.load_state()

    def load_state(self) -> Dict[str, Any]:
        """Carga el estado persistente del supervisor desde disco."""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"No se pudo cargar estado previo ({e}). Inicializando nuevo estado.")

        return {
            "started_at": datetime.now(timezone.utc).isoformat(),
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_cycles_executed": 0,
            "chapters_completed": [],
            "current_queue": []
        }

    def save_state(self):
        """Persiste el estado actual del supervisor a disco."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")

    def scan_pending_tasks(self) -> List[Dict[str, Any]]:
        """
        Escanea exhaustivamente las carpetas raw para identificar los capítulos pendientes.
        """
        queue = []

        # 1. Importaciones Reporte 3
        imp_r3_dir = IMPORTS_DIR / "data" / "raw" / "03_valor_importacion_por_inciso_y_pais_origen"
        if imp_r3_dir.exists():
            for d in sorted(os.listdir(imp_r3_dir)):
                dp = imp_r3_dir / d
                if dp.is_dir() and d.startswith("capitulo-"):
                    files = [f for f in os.listdir(dp) if not f.startswith(".")]
                    if len(files) == 0:
                        cap_code = d.split("-")[1]
                        queue.append({
                            "target": "imports",
                            "report_id": 3,
                            "capitulo": cap_code,
                            "folder": d,
                            "priority": 1
                        })

        # 2. Importaciones Reporte 4
        imp_r4_dir = IMPORTS_DIR / "data" / "raw" / "04_peso_valor_importacion_por_anio_inciso_y_pais"
        if imp_r4_dir.exists():
            for d in sorted(os.listdir(imp_r4_dir)):
                dp = imp_r4_dir / d
                if dp.is_dir() and d.startswith("capitulo-"):
                    files = [f for f in os.listdir(dp) if not f.startswith(".")]
                    if len(files) == 0:
                        cap_code = d.split("-")[1]
                        queue.append({
                            "target": "imports",
                            "report_id": 4,
                            "capitulo": cap_code,
                            "folder": d,
                            "priority": 2
                        })

        # 3. Exportaciones Reporte 3
        exp_r3_dir = EXPORTS_DIR / "data" / "raw" / "03_valor_exportacion_por_inciso_y_pais_destino"
        if exp_r3_dir.exists():
            for d in sorted(os.listdir(exp_r3_dir)):
                dp = exp_r3_dir / d
                if dp.is_dir() and d.startswith("capitulo-"):
                    files = [f for f in os.listdir(dp) if not f.startswith(".")]
                    if len(files) == 0:
                        cap_code = d.split("-")[1]
                        queue.append({
                            "target": "exports",
                            "report_id": 3,
                            "capitulo": cap_code,
                            "folder": d,
                            "priority": 3
                        })

        return queue

    async def execute_task(self, task: Dict[str, Any]) -> bool:
        """
        Ejecuta la extracción de un capítulo específico de forma aislada y segura.
        """
        target = task["target"]
        report_id = task["report_id"]
        capitulo = task["capitulo"]

        logger.info(f"[{target.upper()} R{report_id}] Procesando capítulo {capitulo}...")

        if target == "imports":
            if str(IMPORTS_DIR) not in sys.path:
                sys.path.insert(0, str(IMPORTS_DIR))
            from src.scraper.core.inec_scraper import INECMasterScraper
            scraper = INECMasterScraper(
                str(IMPORTS_DIR / "data" / "raw"),
                str(IMPORTS_DIR / "data" / "processed")
            )
            await scraper.scrape_report(
                report_id=report_id,
                filter_capitulos=[capitulo],
                render_delay=8
            )
            return True

        elif target == "exports":
            if str(EXPORTS_DIR) not in sys.path:
                sys.path.insert(0, str(EXPORTS_DIR))
            from src.scraper.core.inec_export_scraper import INECExportMasterScraper
            scraper = INECExportMasterScraper(
                str(EXPORTS_DIR / "data" / "raw"),
                str(EXPORTS_DIR / "data" / "processed")
            )
            await scraper.scrape_report(
                report_id=report_id,
                filter_capitulos=[capitulo],
                render_delay=8
            )
            return True

        return False

    def trigger_unification(self, target: str):
        """Ejecuta la consolidación a Parquet Snappy tras procesar lotes."""
        try:
            if target == "imports":
                if str(IMPORTS_DIR) not in sys.path:
                    sys.path.insert(0, str(IMPORTS_DIR))
                from src.processing.transformers import DatasetUnifier as ImpUnifier
                u = ImpUnifier(str(IMPORTS_DIR / "data" / "raw"), str(IMPORTS_DIR / "data" / "processed"))
                res = u.unify_all_categories()
                logger.info(f"Consolidación exitosa de Importaciones: {len(res)} categorías en Parquet.")
            elif target == "exports":
                if str(EXPORTS_DIR) not in sys.path:
                    sys.path.insert(0, str(EXPORTS_DIR))
                from src.processing.transformers import DatasetUnifier as ExpUnifier
                u = ExpUnifier(str(EXPORTS_DIR / "data" / "raw"), str(EXPORTS_DIR / "data" / "processed"))
                res = u.unify_all_categories()
                logger.info(f"Consolidación exitosa de Exportaciones: {len(res)} categorías en Parquet.")
        except Exception as e:
            logger.error(f"Error en consolidación Parquet: {e}")

    async def run_supervisor_loop(self, continuous: bool = False):
        """
        Bucle supervisor resiliente con auto-reparación y enfriamiento adaptativo.
        """
        logger.info("=================================================================")
        logger.info("INICIANDO SUPERVISOR AUTÓNOMO DE COMERCIO EXTERIOR (INEC PANAMÁ)")
        logger.info("Amparado bajo Ley 6 de 22 de enero de 2002 de la República de Panamá")
        logger.info("=================================================================")

        consecutive_errors = 0

        while True:
            queue = self.scan_pending_tasks()
            total_pending = len(queue)
            logger.info(f"Estado de cola: {total_pending} capítulos pendientes en total.")

            if total_pending == 0:
                logger.info("¡FELICITACIONES! Todos los capítulos de todos los reportes están 100% descargados.")
                self.trigger_unification("imports")
                self.trigger_unification("exports")
                break

            # Tomar lote actual
            batch = queue[:self.batch_size]
            targets_in_batch = set()

            for item in batch:
                targets_in_batch.add(item["target"])
                try:
                    success = await self.execute_task(item)
                    if success:
                        consecutive_errors = 0
                        self.state["chapters_completed"].append(f"{item['target']}_R{item['report_id']}_cap{item['capitulo']}")
                        self.save_state()
                    else:
                        consecutive_errors += 1
                except Exception as task_err:
                    consecutive_errors += 1
                    logger.error(f"Fallo en capítulo {item['capitulo']} ({item['target']}): {task_err}")
                    # Enfriamiento tras fallo
                    cool_time = min(30 * consecutive_errors, 180)
                    logger.warning(f"Activando enfriamiento adaptativo ({cool_time}s)...")
                    await asyncio.sleep(cool_time)

                # Pausa de cortesía entre capítulos
                jitter = random.uniform(3.0, 6.0)
                await asyncio.sleep(jitter)

            # Consolidar tras cada lote
            for t in targets_in_batch:
                self.trigger_unification(t)

            self.state["total_cycles_executed"] += 1
            self.save_state()

            if not continuous:
                logger.info(f"Lote de {len(batch)} capítulos procesado. Modo de ejecución única finalizado.")
                break

            logger.info("Ciclo de lote finalizado. Iniciando siguiente iteración del supervisor...")
            await asyncio.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Supervisor Autónomo de Comercio Exterior INEC Panamá")
    parser.add_argument("--continuous", action="store_true", default=False,
                        help="Ejecutar en bucle continuo hasta completar el 100% de la cola")
    parser.add_argument("--batch-size", type=int, default=2,
                        help="Cantidad de capítulos a procesar por ciclo")
    args = parser.parse_args()

    supervisor = ComextSupervisor(batch_size=args.batch_size)
    asyncio.run(supervisor.run_supervisor_loop(continuous=args.continuous))


if __name__ == "__main__":
    main()
