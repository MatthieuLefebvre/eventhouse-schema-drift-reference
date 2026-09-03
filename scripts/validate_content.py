from __future__ import annotations

import ast
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN = (
    "thermoking",
    "thermo king",
    "trane",
    "tk2_iot",
    "loadtesting_august",
    "telemetry_schema_drift_test",
    "43a11113-bed7-44c0-9b14-8c16723f1d66",
    "c:\\work\\thermoking",
)
TEXT_SUFFIXES = {".ipynb", ".md", ".kql", ".py", ".json", ".jsonl", ".yml", ".yaml", ".txt"}


def validate_jsonl() -> None:
    rows = []
    for path in (ROOT / "samples").glob("*.jsonl"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                rows.append(json.loads(line))
    assert rows, "No JSONL fixtures found"
    assert {row["sourceType"] for row in rows} == {"controller", "gateway", "cooling_unit"}


def validate_notebooks() -> None:
    for path in (ROOT / "notebooks").glob("*.ipynb"):
        notebook = json.loads(path.read_text(encoding="utf-8"))
        assert notebook.get("nbformat") == 4, f"{path.name}: expected nbformat 4"
        for cell_number, cell in enumerate(notebook.get("cells", []), 1):
            metadata = cell.get("metadata", {})
            assert metadata.get("language"), f"{path.name}: cell {cell_number} has no language"
            assert metadata.get("id"), f"{path.name}: cell {cell_number} has no metadata ID"
            if cell.get("cell_type") != "code":
                continue
            source = "".join(cell.get("source", []))
            if not source.lstrip().startswith("%"):
                ast.parse(source, filename=f"{path.name}:cell-{cell_number}")


def validate_privacy() -> None:
    findings = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES or ".git" in path.parts:
            continue
        if path == Path(__file__).resolve():
            continue
        content = path.read_text(encoding="utf-8").lower()
        for value in FORBIDDEN:
            if value in content:
                findings.append(f"{path.relative_to(ROOT)}: {value}")
    assert not findings, "Forbidden customer content found:\n" + "\n".join(findings)


if __name__ == "__main__":
    validate_jsonl()
    validate_notebooks()
    validate_privacy()
    print("content validation passed")
    sys.exit(0)
