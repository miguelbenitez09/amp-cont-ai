"""Canonical local installer. Environment files are data, never executable code."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_ENV = {"AMP_MODE", "AMP_HOST", "AMP_PORT", "AMP_STATE_DIR"}


def read_environment(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for number, raw in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(f"Línea {number}: se esperaba NOMBRE=valor")
        key, value = (part.strip() for part in line.split("=", 1))
        if key not in ALLOWED_ENV:
            raise ValueError(f"Línea {number}: variable no admitida: {key}")
        if key in result:
            raise ValueError(f"Variable repetida: {key}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if any(char in value for char in ("\x00", "\r", "\n")):
            raise ValueError(f"Valor inválido: {key}")
        result[key] = value
    return result


def validate_environment(values: dict[str, str]) -> None:
    if values.get("AMP_MODE", "portal") not in {"portal", "framework"}:
        raise ValueError("AMP_MODE debe ser portal o framework")
    try:
        port = int(values.get("AMP_PORT", "8000"))
    except ValueError as exc:
        raise ValueError("AMP_PORT debe ser un entero") from exc
    if not 1024 <= port <= 65535:
        raise ValueError("AMP_PORT debe estar entre 1024 y 65535")
    if values.get("AMP_HOST", "127.0.0.1") not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("El instalador local solo permite loopback; exposición externa requiere proxy y TLS")
    state = Path(values.get("AMP_STATE_DIR", ".local/framework"))
    resolved = (ROOT / state).resolve() if not state.is_absolute() else state.resolve()
    lowered = {part.lower() for part in resolved.parts}
    if "_imports" in lowered or "_exports" in lowered:
        raise ValueError("El directorio seleccionado está protegido para adquisición externa")
    if resolved in {ROOT, ROOT.parent, Path.home(), Path(resolved.anchor)}:
        raise ValueError("Seleccione un subdirectorio dedicado al estado de esta instancia")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Instalar o iniciar AMP-CONT-AI")
    parser.add_argument("--mode", choices=["portal", "framework"])
    parser.add_argument("--env-file", type=Path)
    parser.add_argument("--install", action="store_true")
    parser.add_argument("--check", action="store_true", help="Validar sin crear estado")
    parser.add_argument("--no-start", action="store_true")
    args = parser.parse_args(argv)
    try:
        values = {key: os.environ[key] for key in ALLOWED_ENV if key in os.environ}
        if args.env_file:
            values.update(read_environment(args.env_file.resolve()))
        if args.mode:
            values["AMP_MODE"] = args.mode
        if "AMP_MODE" not in values:
            if sys.stdin.isatty() and not args.check:
                choice = input("[1] Predeterminada / [2] Personalizada (.env) / [3] Framework local (1): ").strip()
                if choice == "2":
                    values.update(read_environment(Path(input("Ruta del .env: ").strip()).resolve()))
                else:
                    values["AMP_MODE"] = "framework" if choice == "3" else "portal"
            else:
                values["AMP_MODE"] = "portal"
        validate_environment(values)
        print(f"Modalidad: {values.get('AMP_MODE', 'portal')}")
        if args.check:
            print("Configuración válida. No se inició ningún servicio.")
            return 0
        interpreter = Path(sys.executable)
        if args.install:
            env_dir = ROOT / ".venv"
            venv.EnvBuilder(with_pip=True).create(env_dir)
            interpreter = env_dir / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            subprocess.run([str(interpreter), "-m", "pip", "install", "-r", str(ROOT / "requirements-framework.txt")], check=True)
        elif (ROOT / ".venv").exists():
            candidate = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            if candidate.exists():
                interpreter = candidate
        if args.no_start:
            print("Instalación preparada. Inicie con python scripts/install.py --mode " + values.get("AMP_MODE", "portal"))
            return 0
        host, port = values.get("AMP_HOST", "127.0.0.1"), int(values.get("AMP_PORT", "8000"))
        with socket.socket(socket.AF_INET6 if host == "::1" else socket.AF_INET) as probe:
            if probe.connect_ex((host, port)) == 0:
                raise ValueError(f"Puerto {port} ocupado. El proceso existente se conserva; configure otro puerto.")
        print(f"Portal: http://{host}:{port}/ | Aplicación: /app")
        print("Credencial inicial privada (solo framework): AMP_STATE_DIR/bootstrap-credentials.json")
        return subprocess.call([str(interpreter), "-m", "uvicorn", "src.framework.app:app", "--host", host, "--port", str(port)], cwd=ROOT, env={**os.environ, **values})
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"Instalación detenida: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
