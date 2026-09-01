from __future__ import annotations

import json
import sys
import zipfile
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
TEXT_SUFFIXES = {".md", ".kql", ".py", ".json", ".jsonl", ".yml", ".yaml", ".txt"}


def validate_jsonl() -> None:
    rows = []
    for path in (ROOT / "samples").glob("*.jsonl"):
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                rows.append(json.loads(line))
    assert rows, "No JSONL fixtures found"
    assert {row["sourceType"] for row in rows} == {"controller", "gateway", "cooling_unit"}


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


def validate_presentation() -> None:
    path = ROOT / "presentation" / "eventhouse-schema-drift-reference.pptx"
    if not path.exists():
        return
    assert zipfile.is_zipfile(path), "Presentation is not a valid Open XML package"
    with zipfile.ZipFile(path) as package:
        slides = [name for name in package.namelist() if name.startswith("ppt/slides/slide") and name.endswith(".xml")]
    assert len(slides) == 18, f"Expected 18 slides, found {len(slides)}"


if __name__ == "__main__":
    validate_jsonl()
    validate_privacy()
    validate_presentation()
    print("content validation passed")
    sys.exit(0)
