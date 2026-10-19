import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def main():
    workflow = yaml.safe_load(
        (ROOT / "ci/github-actions.yml").read_text(encoding="utf-8")
    )
    render = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    contract = json.loads((ROOT / "contracts/openapi.json").read_text(encoding="utf-8"))
    assert {"checks", "backend", "frontend", "e2e", "package", "deploy"} <= workflow[
        "jobs"
    ].keys()
    assert "concurrency" in workflow and ("on" in workflow or True in workflow)
    assert all(
        r.get("region") == "frankfurt"
        for r in render["databases"] + render["services"]
        if r.get("runtime") != "static"
    )
    assert "/products/{product_id}/price-history" in contract["paths"]
    assert {"ProductOut", "ProductPage", "OrderOut"} <= contract["components"][
        "schemas"
    ].keys()
    assert (ROOT / "backend/requirements.lock").exists() and (
        ROOT / "frontend/package-lock.json"
    ).exists()
    print("Configuración, contrato, fases de CI y archivos de dependencias: OK")
    print("Esta validación local no ejecuta ni publica workflows o recursos externos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
