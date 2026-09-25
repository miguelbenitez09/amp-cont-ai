# Makefile for Panama PortOps-AI MLOps Platform
# Follows MLOps Masterclass Section 55

.PHONY: help install download-data classify normalize quality features eda train register serve monitor dashboard test profile-distributions simulate stress-test docker-build docker-up docker-down all

help:
	@echo "Available commands for Panama PortOps-AI:"
	@echo "  make install               - Install python dependencies in editable mode"
	@echo "  make download-data         - Download official AMP datasets (2015-2026) from datosabiertos.gob.pa"
	@echo "  make classify              - Run dataset taxonomy and classification on 353 datasets"
	@echo "  make normalize             - Execute Medallion Silver transformation (Parquet)"
	@echo "  make quality               - Run Data Quality Gates validation"
	@echo "  make features              - Generate Gold Feature Store tables"
	@echo "  make eda                   - Execute Exploratory Data Analysis and statistical profiling"
	@echo "  make train                 - Train LightGBM quantiles with Expanding Window in MLflow"
	@echo "  make register              - Promote Champion model in MLflow Model Registry"
	@echo "  make profile-distributions - Profile distributions, KS test and Cholesky factorization"
	@echo "  make simulate              - Run Monte Carlo stochastic simulation engine"
	@echo "  make stress-test           - Execute multi-scenario stress test & reverse stress testing"
	@echo "  make serve                 - Launch FastAPI serving microservice on port 8000"
	@echo "  make monitor               - Execute Evidently AI Data and Concept Drift analysis"
	@echo "  make dashboard             - Launch Streamlit executive simulation dashboard on port 8501"
	@echo "  make test                  - Run full pytest test suite (25 tests)"
	@echo "  make docker-build          - Build production multi-stage Docker image"
	@echo "  make docker-up             - Launch full stack with Docker Compose"
	@echo "  make docker-down           - Stop Docker Compose stack"
	@echo "  make all                   - Run complete pipeline from data to trained model"

install:
	pip install -e .

download-data:
	python scripts/download_data.py

classify:
	python -m src.data.classifier

normalize:
	python -m src.data.normalizer

quality:
	python -m src.data.quality

features:
	python -m src.features.feature_store

eda:
	python -m analysis.eda_deep_dive

train:
	python -m src.models.train

register:
	python -m src.models.registry

profile-distributions:
	python -m src.simulation.distribution_profiler

simulate:
	python -m src.simulation.monte_carlo_engine

stress-test:
	python -m src.simulation.stress_tester

serve:
	uvicorn src.serving.api:app --host 0.0.0.0 --port 8000 --reload

monitor:
	python -m src.monitoring.drift

dashboard:
	streamlit run apps/dashboard.py

test:
	pytest -v tests/

docker-build:
	docker build -t panama-portops-ai:latest .

docker-up:
	docker compose up -d

docker-down:
	docker compose down

all: classify normalize quality features train register monitor test
