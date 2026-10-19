import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser(
        description="Smoke tests de la tienda desplegada o local"
    )
    parser.add_argument("--url", default="http://localhost:18000")
    args = parser.parse_args()
    try:
        for path in ["/health", "/version", "/products?limit=1", "/categories"]:
            with urlopen(args.url.rstrip("/") + path, timeout=10) as response:
                data = json.load(response)
                if path == "/health" and data.get("status") != "ok":
                    raise ValueError("La BD no está sana")
                print("OK", path, response.status)
        return 0
    except (URLError, ValueError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
