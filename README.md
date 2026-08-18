# llm-doc-parser

Turn any document — PDF, web page, image export, or spreadsheet — into clean, validated JSON with an LLM.

This is a small, runnable demo of a pattern I build in production: **multi-format ingest → LLM extraction → schema validation**. At FlowSpace I use the same shape in a listing bot that reads a workspace-provider brochure (in any format) and drafts a structured listing for human review before it hits the backend.

## Why it's useful
- One command turns messy source docs into a fixed JSON schema.
- **No hallucinated fields:** the prompt forces exactly the keys you ask for, `null` when absent, and the code rejects a response that drops a field.
- Swap the field list per use case — no code change.

## Install
```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-...
```

## Use
```bash
python parser.py brochure.pdf --fields title,company,location,price,summary
```
```json
{
  "title": "Flexible desks at Aviation House",
  "company": "Example Workspaces",
  "location": "London, UK",
  "price": "£350/desk/month",
  "summary": "12 hot desks and two meeting rooms, 24/7 access."
}
```

## How it works
1. **Ingest** — reads `.txt`, `.md`, `.csv` directly; `.pdf` via `pypdf`.
2. **Extract** — builds a schema-locked prompt and calls Claude.
3. **Validate** — parses the JSON, strips code fences, and errors if the model omitted a requested field. Extra keys are dropped.

## Extend
- Add image/OCR ingest for scanned brochures.
- Batch a folder and write one row per file.
- Wrap `extract()` in an n8n / webhook step for a human-in-the-loop review queue (how the production version runs).

---
Built by [Prabhavit Gupta](https://www.linkedin.com/in/prabhavit/) — AI & automation engineer.
