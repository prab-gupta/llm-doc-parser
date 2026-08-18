"""
llm-doc-parser — turn any document into structured JSON with an LLM.

Demo of the multi-format ingest -> extract -> validate pipeline I build in
production (e.g. a listing bot that drafts structured listings from brochures).

Usage:
    export ANTHROPIC_API_KEY=sk-...
    python parser.py sample.txt --fields title,company,location,price,summary
"""
import argparse
import json
import os
import sys
from pathlib import Path

import anthropic  # pip install anthropic


def read_document(path: Path) -> str:
    """Extract plain text from txt/md/csv, or pdf if pypdf is installed."""
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader  # pip install pypdf
        except ImportError:
            sys.exit("PDF support needs pypdf: pip install pypdf")
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    sys.exit(f"Unsupported file type: {suffix}")


def build_prompt(text: str, fields: list[str]) -> str:
    schema = ", ".join(f'"{f}": string|null' for f in fields)
    return (
        "Extract the following fields from the document and return ONLY valid "
        f"JSON with exactly these keys: {{{schema}}}. "
        "Use null when a field is not present. Do not invent values.\n\n"
        f"DOCUMENT:\n{text[:12000]}"
    )


def extract(text: str, fields: list[str], model: str) -> dict:
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=model,
        max_tokens=1024,
        messages=[{"role": "user", "content": build_prompt(text, fields)}],
    )
    raw = msg.content[0].text.strip()
    # tolerate code fences the model may add
    if raw.startswith("```"):
        raw = raw.split("```")[1].lstrip("json").strip()
    data = json.loads(raw)
    # validate: exactly the requested keys, no extras, no hallucinated fields
    missing = [f for f in fields if f not in data]
    if missing:
        raise ValueError(f"Model omitted fields: {missing}")
    return {f: data[f] for f in fields}


def main() -> None:
    ap = argparse.ArgumentParser(description="Document -> structured JSON via LLM")
    ap.add_argument("file", type=Path)
    ap.add_argument("--fields", required=True, help="comma-separated field names")
    ap.add_argument("--model", default="claude-sonnet-5")
    args = ap.parse_args()

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    text = read_document(args.file)
    result = extract(text, fields, args.model)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
