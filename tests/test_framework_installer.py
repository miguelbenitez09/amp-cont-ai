from pathlib import Path
import pytest
from scripts.install import read_environment, validate_environment, main


def test_env_is_data_and_never_executes(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("AMP_MODE=portal\nAMP_STATE_DIR='$(whoami)'\n", encoding="utf-8")
    assert read_environment(env)["AMP_STATE_DIR"] == "$(whoami)"


def test_duplicate_and_unknown_env_rejected(tmp_path: Path):
    env = tmp_path / ".env"
    env.write_text("AMP_MODE=portal\nAMP_MODE=framework\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_environment(env)
    env.write_text("UNREVIEWED_SECRET=anything\n", encoding="utf-8")
    with pytest.raises(ValueError):
        read_environment(env)


@pytest.mark.parametrize("value", ["data/_imports/output", "data/_exports/output"])
def test_protected_paths_rejected_without_access(value):
    with pytest.raises(ValueError, match="protegido"):
        validate_environment({"AMP_STATE_DIR": value})


def test_public_bind_rejected():
    with pytest.raises(ValueError, match="loopback"):
        validate_environment({"AMP_HOST": "0.0.0.0"})


def test_check_does_not_create_state(tmp_path, monkeypatch):
    state = tmp_path / "uncreated"
    monkeypatch.setenv("AMP_STATE_DIR", str(state))
    assert main(["--check", "--mode", "portal"]) == 0
    assert not state.exists()
