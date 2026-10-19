import argparse
import subprocess
from datetime import UTC, datetime
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Backup lógico de la BD local de esta práctica"
    )
    parser.add_argument("--salida", type=Path)
    args = parser.parse_args()
    output = args.salida or root / ".artifacts" / (
        "backup-" + datetime.now(UTC).strftime("%Y%m%d-%H%M%S") + ".sql"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("wb") as file:
        subprocess.run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "db",
                "pg_dump",
                "-U",
                "shop",
                "-d",
                "shop",
                "--no-owner",
                "--no-acl",
                "--schema=public",
            ],
            cwd=root,
            stdout=file,
            check=True,
        )
    print(output)


if __name__ == "__main__":
    main()
