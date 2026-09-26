"""
Inspection Script for Local LLM Runtimes (Ollama & vLLM)
Detects available models, quantizations, and inference endpoints.

Author: Desarrollado v1.0 Miguel Benítez
License: GNU General Public License v3.0 (GPL-3.0) with Section 7 Attribution
"""

import sys
import json
import requests

# Ensure UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")


def check_ollama_models(base_url="http://localhost:11434"):
    print("🔍 Inspeccionando servidor Ollama...")
    try:
        response = requests.get(f"{base_url}/api/tags", timeout=3)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ Ollama activo en {base_url}. Modelos encontrados ({len(models)}):")
            for m in models:
                size_gb = m.get("size", 0) / (1024 ** 3)
                modified = m.get("modified_at", "N/A")[:10]
                print(f"  • {m.get('name'):<30} | Tamaño: {size_gb:.2f} GB | Modificado: {modified}")
            return models
        else:
            print(f"⚠️ Ollama respondió con código de estado: {response.status_code}")
    except Exception as e:
        print(f"ℹ️ Ollama no detectado en {base_url} ({e})")
    return []


def check_vllm_models(base_url="http://localhost:8000"):
    print("\n🔍 Inspeccionando servidor vLLM (OpenAI-Compatible API)...")
    try:
        response = requests.get(f"{base_url}/v1/models", timeout=3)
        if response.status_code == 200:
            models = response.json().get("data", [])
            print(f"✅ vLLM activo en {base_url}. Modelos cargados ({len(models)}):")
            for m in models:
                print(f"  • ID Modelo: {m.get('id'):<30} | Propietario: {m.get('owned_by', 'vllm')}")
            return models
        else:
            print(f"⚠️ vLLM respondió con código de estado: {response.status_code}")
    except Exception as e:
        print(f"ℹ️ vLLM no detectado en {base_url} ({e})")
    return []


if __name__ == "__main__":
    print("=" * 75)
    print("Panamá PortOps-AI v2.0 — Verificador de Motores LLM Locales")
    print("Firma Oficial: Desarrollado v1.0 Miguel Benítez")
    print("=" * 75)
    ollama_list = check_ollama_models()
    vllm_list = check_vllm_models()
    print("=" * 75)
