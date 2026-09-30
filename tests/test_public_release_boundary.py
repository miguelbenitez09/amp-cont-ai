"""Public packaging tests use temporary fixtures only."""
import json
from pathlib import Path
import zipfile
import pytest
from scripts.verify_public_release import audit, selected_files
from scripts.build_public_release import build

def fixture_root(tmp_path, include=None):
    policy = tmp_path / "brain/releases/PUBLIC_FILE_ALLOWLIST.yaml"
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps({"version": 2, "include": include or ["public/*"], "required": []}), encoding="utf-8")
    (tmp_path / "public").mkdir()
    return tmp_path

def test_only_allowlisted_files_enter_archive(tmp_path):
    root = fixture_root(tmp_path)
    (root / "public/readme.md").write_text("Public documentation")
    (root / ".env").write_text("SECRET=private")
    out = root / "release.zip"
    build(root, out)
    with zipfile.ZipFile(out) as archive:
        assert set(archive.namelist()) == {"public/readme.md", "PUBLIC_MANIFEST.json"}
        manifest = json.loads(archive.read("PUBLIC_MANIFEST.json"))
        assert len(manifest["files"][0]["sha256"]) == 64

@pytest.mark.parametrize("pattern", ["../*", "/etc/*", "C:/private/*", "public/../../*"])
def test_policy_cannot_escape_root(tmp_path, pattern):
    root = fixture_root(tmp_path, [pattern])
    with pytest.raises(ValueError, match="unsafe"):
        selected_files(root)

@pytest.mark.parametrize("name,payload", [
    ("state.db", b"state"), ("weights.bin", b"model"),
    ("page.html", b"hello\x00secret"), ("a.py", b"from src.data import scraper"),
    ("note.md", b"-----BEGIN PRIVATE KEY-----"),
    (".env.example", b"API_KEY=example-real-secret"),
])
def test_disguised_and_forbidden_payloads_block_build(tmp_path, name, payload):
    root = fixture_root(tmp_path)
    (root / "public" / name).write_bytes(payload)
    assert audit(root)["violations"]
    with pytest.raises(ValueError, match="blocked"):
        build(root, root / "release.zip")
    assert not (root / "release.zip").exists()

def test_empty_secret_template_is_allowed(tmp_path):
    root = fixture_root(tmp_path)
    (root / "public/.env.example").write_text("API_KEY=\nAMP_MODE=portal\n")
    assert not audit(root)["violations"]

def test_symlink_is_rejected(tmp_path):
    root = fixture_root(tmp_path)
    target = root / "secret.txt"
    target.write_text("private")
    try:
        (root / "public/link.txt").symlink_to(target)
    except OSError:
        pytest.skip("Host does not permit creating symlinks")
    with pytest.raises(ValueError, match="Linked"):
        selected_files(root)

def test_existing_output_is_never_overwritten(tmp_path):
    root = fixture_root(tmp_path)
    out = root / "release.zip"
    out.write_bytes(b"original")
    with pytest.raises(FileExistsError):
        build(root, out)
    assert out.read_bytes() == b"original"
