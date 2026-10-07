import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_frontend_package_manager_is_pnpm_only():
    package_json = json.loads((PROJECT_ROOT / "package.json").read_text(encoding="utf-8"))

    assert package_json["packageManager"].startswith("pnpm@")
    assert package_json["scripts"]["preinstall"] == "node scripts/ensure_pnpm.js"
    assert (PROJECT_ROOT / "scripts" / "ensure_pnpm.js").exists()
    assert (PROJECT_ROOT / "pnpm-workspace.yaml").exists()


def test_forbidden_javascript_lockfiles_are_absent():
    forbidden = ["package-lock.json", "npm-shrinkwrap.json", "yarn.lock"]

    assert [name for name in forbidden if (PROJECT_ROOT / name).exists()] == []
