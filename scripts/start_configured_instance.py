"""Start both listeners from the saved control-plane configuration.

Stop the existing instance before invoking this launcher. --dry-run checks the
plan without starting processes or exposing environment variables or secrets.
"""
from pathlib import Path
import argparse
import json
import os
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

def plan(database):
    from src.serving.workspace_router import DEFAULT_CONFIG, validate_config
    config = DEFAULT_CONFIG
    with sqlite3.connect(database) as db:
        try:
            row = db.execute('SELECT value FROM workspace_config WHERE id=1').fetchone()
        except sqlite3.OperationalError:
            row = None
    if row:
        config = json.loads(row[0])
    validate_config(config)
    return config

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--database', type=Path, default=ROOT/'data/enterprise_db/portops_platform.db')
    args = parser.parse_args()
    config = plan(args.database)
    executable = ROOT/'bin/gateway.exe'
    if not executable.is_file():
        raise SystemExit('Compile primero el gateway en bin/gateway.exe.')
    print(json.dumps({'gateway_port':config['gateway_port'], 'api_port':config['api_port'],
                      'paths':config['paths'], 'restart_required':True}, indent=2))
    if args.dry_run:
        return
    environment = dict(os.environ)
    environment.update(config['environment'])
    environment.update(PORT=str(config['gateway_port']),
                       UPSTREAM_URL=f"http://127.0.0.1:{config['api_port']}",
                       STATIC_DIR=str(ROOT/'src/serving/static'))
    for name, path in config['paths'].items():
        directory = (ROOT/path).resolve()
        directory.mkdir(parents=True, exist_ok=True)
        environment['PORTOPS_'+name.upper()+'_PATH'] = str(directory)
    flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
    processes = []
    try:
        processes.append(subprocess.Popen([sys.executable, '-m', 'uvicorn', 'src.serving.api:app',
            '--host', '127.0.0.1', '--port', str(config['api_port'])], cwd=ROOT, env=environment, creationflags=flags))
        processes.append(subprocess.Popen([str(executable)], cwd=ROOT, env=environment, creationflags=flags))
        import time
        while all(process.poll() is None for process in processes):
            time.sleep(.5)
        raise SystemExit('Un proceso terminó. Revise sus mensajes y puertos ocupados.')
    except KeyboardInterrupt:
        pass
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

if __name__ == '__main__':
    sys.path.insert(0, str(ROOT))
    main()
