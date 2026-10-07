from pathlib import Path


def test_vllm_compose_is_opt_in_and_binds_loopback():
    text = (Path("infra/vllm/docker-compose.vllm.yml")).read_text(encoding="utf-8")
    assert "profiles: [\"vllm\"]" in text
    assert '127.0.0.1:8080:8000' in text
    assert "VLLM_API_KEY:?set VLLM_API_KEY" in text
    assert "--enable-prefix-caching" in text
    assert "--enable-chunked-prefill" in text
    assert "vllm-cpu:" in text
    assert "shm_size: \"1gb\"" in text
    assert "Qwen/Qwen2.5-0.5B-Instruct" in text
