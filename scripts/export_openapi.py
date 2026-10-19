import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.main import app


def main():
    directory = ROOT / "contracts"
    directory.mkdir(exist_ok=True)
    contract = app.openapi()
    contract["servers"] = [
        {"url": "http://localhost:18000/v1", "description": "API local versionada"}
    ]
    (directory / "openapi.json").write_text(
        json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (directory / "openapi.yaml").write_text(
        yaml.safe_dump(contract, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    print("Contrato OpenAPI exportado desde la implementación real")


if __name__ == "__main__":
    main()
