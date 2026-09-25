"""
Panama PortOps-AI: Automated Open Data Downloader
Downloads official maritime statistics from datosabiertos.gob.pa (Autoridad Marítima de Panamá)
Strictly adheres to Ley 6 de 2002 de Transparencia de la República de Panamá.
Author: Desarrollado v1.0 Miguel Benítez
"""

import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from download_amp_datasets import main as run_download

if __name__ == "__main__":
    print("=" * 70)
    print("PANAMA PORTOPS-AI: DESCARGA DE DATOS ABIERTOS AMP (2015-2026)")
    print("Autoridad Marítima de Panamá - Portal de Datos Abiertos de Panamá")
    print("Marco Legal: Ley 6 de 22 de enero de 2002 (Transparencia en la Gestión Pública)")
    print("Desarrollado v1.0 Miguel Benítez")
    print("=" * 70)
    run_download()
