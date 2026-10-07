"""Local, auditable numeric model workflow. No network and no pickle loading.

Datasets require explicit local review. That review never approves publication.
Time order is used for validation; normalization fits the training partition only.
"""
from __future__ import annotations

import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import sqlite3
import uuid


RECIPES = [
    {"id": "mean_baseline", "name": "Referencia de media", "algorithm": "mean", "description": "Predice la media del período de entrenamiento. Útil para comprobar si un modelo más complejo aporta mejora.", "parameters": {}, "limitations": "No representa tendencia ni estacionalidad."},
    {"id": "linear_baseline", "name": "Regresión lineal regularizada", "algorithm": "ridge", "description": "Aprende una relación lineal con variables numéricas disponibles al momento de predecir.", "parameters": {"alpha": 1.0}, "limitations": "No extrapola cambios de régimen con fiabilidad. Seleccione únicamente variables conocidas en la fecha de predicción."},
]
SENSITIVE = re.compile(r"(^|_)(name|nombre|empresa|company|ruc|cedula|passport|pasaporte|email|correo|phone|telefono|contacto|account|cuenta|address|direccion|consignee|consignatario|id)(_|$)", re.I)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def solve(matrix: list[list[float]], vector: list[float]) -> list[float]:
    """Pivoted Gaussian elimination for a maximum of 13 coefficients."""
    work = [row[:] + [value] for row, value in zip(matrix, vector)]
    n = len(work)
    for col in range(n):
        pivot = max(range(col, n), key=lambda row: abs(work[row][col]))
        work[col], work[pivot] = work[pivot], work[col]
        scale = work[col][col]
        if abs(scale) < 1e-12:
            raise ValueError("Matriz singular: reduzca variables redundantes")
        work[col] = [value / scale for value in work[col]]
        for row in range(n):
            if row != col:
                factor = work[row][col]
                work[row] = [a - factor * b for a, b in zip(work[row], work[col])]
    return [row[-1] for row in work]


class ModelService:
    def __init__(self, db_path: Path, state_dir: Path):
        self.db_path, self.state_dir = Path(db_path), Path(state_dir)

    def connect(self):
        conn = sqlite3.connect(self.db_path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=15000")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def initialize(self):
        with self.connect() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS fw_datasets (
                  id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL,
                  content_sha256 TEXT NOT NULL, date_column TEXT NOT NULL,
                  target_column TEXT NOT NULL, features_json TEXT NOT NULL,
                  rows_json TEXT NOT NULL, review_status TEXT NOT NULL,
                  reviewed_by TEXT, reviewed_at TEXT);
                CREATE TABLE IF NOT EXISTS fw_training_runs (
                  id TEXT PRIMARY KEY, dataset_id TEXT NOT NULL REFERENCES fw_datasets(id),
                  created_at TEXT NOT NULL, actor TEXT NOT NULL, recipe_id TEXT NOT NULL,
                  metrics_json TEXT NOT NULL, split_json TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS fw_models (
                  id TEXT PRIMARY KEY, run_id TEXT NOT NULL REFERENCES fw_training_runs(id),
                  dataset_id TEXT NOT NULL, created_at TEXT NOT NULL,
                  artifact_json TEXT NOT NULL, artifact_sha256 TEXT NOT NULL);
            ''')

    def import_csv(self, name: str, csv_text: str, date_column: str, target_column: str, feature_columns: list[str]):
        if not name.strip() or len(name) > 120:
            raise ValueError("Nombre requerido, máximo 120 caracteres")
        if len(csv_text.encode("utf-8")) > 2_000_000:
            raise ValueError("CSV supera 2 MB")
        if not 1 <= len(feature_columns) <= 12:
            raise ValueError("Seleccione entre 1 y 12 variables numéricas")
        chosen = [date_column, target_column, *feature_columns]
        if len(set(chosen)) != len(chosen):
            raise ValueError("Fecha, target y variables deben ser columnas diferentes")
        reader = csv.DictReader(io.StringIO(csv_text.lstrip("\ufeff")))
        headers = reader.fieldnames or []
        if len(set(headers)) != len(headers) or set(headers) != set(chosen):
            raise ValueError("Incluya solamente las columnas declaradas, sin duplicados ni campos adicionales")
        if any(SENSITIVE.search(column.replace("-", "_").replace(" ", "_")) for column in headers):
            raise ValueError("El archivo contiene campos potencialmente identificadores; elimínelos antes de importar")
        rows = []
        for raw in reader:
            if len(rows) >= 10000 or None in raw or any(value is None for value in raw.values()):
                raise ValueError("CSV inválido o más de 10000 filas")
            try:
                # Canonical dates avoid ambiguous ordering and locale-dependent parsing.
                date = datetime.strptime(raw[date_column], "%Y-%m-%d").date().isoformat()
                numeric = {column: float(raw[column]) for column in [target_column, *feature_columns]}
            except (ValueError, TypeError) as exc:
                raise ValueError("Fecha ISO YYYY-MM-DD y valores numéricos completos requeridos") from exc
            if any(not math.isfinite(value) or abs(value) > 1e12 for value in numeric.values()):
                raise ValueError("Valores no finitos o fuera de rango")
            rows.append({date_column: date, **numeric})
        if len(rows) < 10:
            raise ValueError("Se requieren al menos 10 observaciones temporales")
        rows.sort(key=lambda row: row[date_column])
        if len({row[date_column] for row in rows}) != len(rows):
            raise ValueError("Esta receta requiere una observación por fecha; agregue o separe series")
        dataset_id = uuid.uuid4().hex
        canonical = json.dumps(rows, sort_keys=True, ensure_ascii=False, allow_nan=False)
        with self.connect() as db:
            db.execute("INSERT INTO fw_datasets VALUES (?,?,?,?,?,?,?,?,?,?,?)", (dataset_id, name.strip(), now(), hashlib.sha256(canonical.encode()).hexdigest(), date_column, target_column, json.dumps(feature_columns), canonical, "REVIEW_REQUIRED", None, None))
        return {"id": dataset_id, "name": name.strip(), "rows": len(rows), "review_status": "REVIEW_REQUIRED", "publication_status": "NOT_APPROVED", "notice": "Revise procedencia, derechos, privacidad y disponibilidad temporal. La revisión local no autoriza publicación."}

    def list_datasets(self):
        with self.connect() as db:
            rows = db.execute("SELECT id,name,created_at,content_sha256,date_column,target_column,features_json,review_status,reviewed_by,reviewed_at FROM fw_datasets ORDER BY created_at DESC").fetchall()
        return [{**dict(row), "feature_columns": json.loads(row["features_json"]), "publication_status": "NOT_APPROVED"} for row in rows]

    def review(self, dataset_id: str, actor: str):
        with self.connect() as db:
            result = db.execute("UPDATE fw_datasets SET review_status='LOCAL_REVIEWED',reviewed_by=?,reviewed_at=? WHERE id=?", (actor, now(), dataset_id))
            if not result.rowcount:
                raise ValueError("Dataset no encontrado")
        return {"id": dataset_id, "review_status": "LOCAL_REVIEWED", "publication_status": "NOT_APPROVED"}

    def recipes(self):
        return RECIPES

    def train(self, dataset_id: str, recipe_id: str, actor: str):
        if recipe_id not in {item["id"] for item in RECIPES}:
            raise ValueError("Receta no soportada")
        with self.connect() as db:
            dataset = db.execute("SELECT * FROM fw_datasets WHERE id=?", (dataset_id,)).fetchone()
        if not dataset or dataset["review_status"] != "LOCAL_REVIEWED":
            raise ValueError("El dataset requiere revisión local antes de entrenar")
        rows, features = json.loads(dataset["rows_json"]), json.loads(dataset["features_json"])
        cut = max(8, int(len(rows) * .8))
        train, test = rows[:cut], rows[cut:]
        target = dataset["target_column"]
        means = [sum(row[col] for row in train) / len(train) for col in features]
        scales = [(sum((row[col] - mean) ** 2 for row in train) / len(train)) ** .5 or 1.0 for col, mean in zip(features, means)]
        design = [[1.0] + [(row[col] - mean) / scale for col, mean, scale in zip(features, means, scales)] for row in train]
        if recipe_id == "mean_baseline":
            coeff = [sum(row[target] for row in train) / len(train)] + [0.] * len(features)
        else:
            size = len(features) + 1
            gram = [[sum(row[i] * row[j] for row in design) + (1.0 if i == j and i > 0 else 0.0) for j in range(size)] for i in range(size)]
            vector = [sum(row[i] * obs[target] for row, obs in zip(design, train)) for i in range(size)]
            coeff = solve(gram, vector)
        artifact = {"format": "amp-linear-v1", "features": features, "target": target, "means": means, "scales": scales, "coefficients": coeff, "recipe_id": recipe_id, "dataset_sha256": dataset["content_sha256"], "trained_at": now(), "data_status": "USER_PROVIDED", "publication_status": "NOT_APPROVED"}
        predictions = [self.evaluate(artifact, row) for row in test]
        errors = [abs(pred - row[target]) for pred, row in zip(predictions, test)]
        denominator = sum(abs(row[target]) for row in test)
        metrics = {"mae": sum(errors) / len(errors), "rmse": math.sqrt(sum(err * err for err in errors) / len(errors)), "wape": sum(errors) / denominator if denominator else None, "validation_rows": len(test)}
        split = {"strategy": "chronological_holdout_80_20", "training_rows": len(train), "validation_rows": len(test), "train_end": train[-1][dataset["date_column"]], "validation_start": test[0][dataset["date_column"]], "warning": "Un holdout no reemplaza backtesting. El usuario debe revisar fuga temporal en las variables."}
        model_id, run_id = uuid.uuid4().hex, uuid.uuid4().hex
        payload = json.dumps(artifact, sort_keys=True, allow_nan=False)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        with self.connect() as db:
            db.execute("INSERT INTO fw_training_runs VALUES (?,?,?,?,?,?,?)", (run_id, dataset_id, now(), actor, recipe_id, json.dumps(metrics), json.dumps(split)))
            db.execute("INSERT INTO fw_models VALUES (?,?,?,?,?,?)", (model_id, run_id, dataset_id, now(), payload, digest))
        return {"id": run_id, "model_id": model_id, "status": "COMPLETED", "metrics": metrics, "split": split, "artifact_sha256": digest}

    @staticmethod
    def evaluate(artifact: dict, values: dict):
        prediction = artifact["coefficients"][0]
        for col, mean, scale, coefficient in zip(artifact["features"], artifact["means"], artifact["scales"], artifact["coefficients"][1:]):
            value = float(values[col])
            if not math.isfinite(value) or abs(value) > 1e12:
                raise ValueError("Valor de inferencia inválido")
            prediction += coefficient * (value - mean) / scale
        if not math.isfinite(prediction):
            raise ValueError("Resultado no finito")
        return prediction

    def artifact(self, model_id: str):
        with self.connect() as db:
            model = db.execute("SELECT artifact_json,artifact_sha256 FROM fw_models WHERE id=?", (model_id,)).fetchone()
        if not model:
            raise ValueError("Modelo no encontrado")
        if hashlib.sha256(model["artifact_json"].encode()).hexdigest() != model["artifact_sha256"]:
            raise ValueError("Falló la verificación de integridad del artefacto")
        return {"model_id": model_id, "sha256": model["artifact_sha256"], "artifact": json.loads(model["artifact_json"])}

    def predict(self, model_id: str, features: dict):
        model = self.artifact(model_id)
        if set(features) != set(model["artifact"]["features"]):
            raise ValueError("Las variables deben coincidir exactamente con la firma del modelo")
        return {"model_id": model_id, "prediction": self.evaluate(model["artifact"], features), "target": model["artifact"]["target"], "artifact_sha256": model["sha256"]}

    def models(self):
        with self.connect() as db:
            rows = db.execute("SELECT m.id,m.run_id,m.dataset_id,m.created_at,m.artifact_sha256,r.recipe_id,r.metrics_json,r.split_json FROM fw_models m JOIN fw_training_runs r ON r.id=m.run_id ORDER BY m.created_at DESC").fetchall()
        return [{**dict(row), "metrics": json.loads(row["metrics_json"]), "split": json.loads(row["split_json"]), "status": "LOCAL_TRAINED", "publication_status": "NOT_APPROVED"} for row in rows]

    def datasets(self):
        with self.connect() as db:
            rows = db.execute("SELECT id,name,created_at,content_sha256,date_column,target_column,features_json,review_status,reviewed_by,reviewed_at FROM fw_datasets ORDER BY created_at DESC").fetchall()
        result = []
        for row in rows:
            item = dict(row)
            item["features"] = json.loads(item.pop("features_json"))
            result.append(item)
        return result
