from datetime import date, timedelta
import sqlite3

import pytest
from src.framework.ml import ModelService


@pytest.fixture
def service(tmp_path):
    result = ModelService(tmp_path / "test.db", tmp_path)
    result.initialize()
    return result


def dataset_text():
    lines = ["date,demand,lag_demand"]
    for i in range(30):
        lines.append(f"{date(2020,1,1)+timedelta(days=i)},{3*i+2},{i}")
    return "\n".join(lines)


def test_train_review_predict_and_integrity(service):
    dataset = service.import_csv("Synthetic test", dataset_text(), "date", "demand", ["lag_demand"])
    with pytest.raises(ValueError, match="revisión"):
        service.train(dataset["id"], "linear_baseline", "test")
    service.review(dataset["id"], "test")
    run = service.train(dataset["id"], "linear_baseline", "test")
    assert run["metrics"]["mae"] < 3
    assert run["split"]["train_end"] < run["split"]["validation_start"]
    assert abs(service.predict(run["model_id"], {"lag_demand": 25})["prediction"] - 77) < 3
    assert service.artifact(run["model_id"])["artifact"]["publication_status"] == "NOT_APPROVED"
    with sqlite3.connect(service.db_path) as db:
        db.execute("UPDATE fw_models SET artifact_sha256='tampered'")
    with pytest.raises(ValueError, match="integridad"):
        service.predict(run["model_id"], {"lag_demand": 25})


def test_unknown_fields_and_sensitive_names_rejected(service):
    with pytest.raises(ValueError, match="columnas"):
        service.import_csv("test", dataset_text(), "date", "demand", ["other"])
    with pytest.raises(ValueError, match="identificadores"):
        service.import_csv("test", dataset_text().replace("lag_demand", "ruc"), "date", "demand", ["ruc"])


def test_nonfinite_and_duplicate_time_rejected(service):
    with pytest.raises(ValueError, match="finitos"):
        service.import_csv("test", dataset_text().replace(",2,0", ",nan,0"), "date", "demand", ["lag_demand"])
    with pytest.raises(ValueError, match="observación"):
        service.import_csv("test", dataset_text().replace("2020-01-02", "2020-01-01"), "date", "demand", ["lag_demand"])
