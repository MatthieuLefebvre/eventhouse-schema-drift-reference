from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SUPPORTED_TYPES = {"bool", "datetime", "decimal", "dynamic", "guid", "int", "long", "real", "string", "timespan"}


def require_identifier(value: str) -> str:
    if not IDENTIFIER.fullmatch(value):
        raise ValueError(f"Unsafe Kusto identifier: {value!r}")
    return value


def emit_command(request: dict[str, str]) -> str:
    table = require_identifier(request["table"])
    column = require_identifier(request["column"])
    data_type = request["type"].lower()
    if data_type not in SUPPORTED_TYPES:
        raise ValueError(f"Unsupported Kusto type: {data_type!r}")
    return f".alter-merge table {table} ({column}:{data_type})"


def main() -> None:
    parser = argparse.ArgumentParser(description="Emit reviewed Eventhouse column-promotion DDL")
    parser.add_argument("request", type=Path, help="Approved promotion request JSON")
    parser.add_argument("--execute", action="store_true", help="Reserved; direct execution is intentionally unsupported")
    args = parser.parse_args()
    if args.execute:
        raise SystemExit("Direct execution is intentionally unsupported. Review and run the emitted KQL manually.")
    request = json.loads(args.request.read_text(encoding="utf-8"))
    if request.get("approved") is not True:
        raise SystemExit("Promotion request must contain approved=true")
    print(emit_command(request))


if __name__ == "__main__":
    main()
