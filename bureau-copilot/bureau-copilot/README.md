# Bureaucracy Copilot

**An autonomous agent for risky government and institutional forms. It does not just draft answers: it identifies dangerous fields, resolves what it safely can from applicant context, and clearly flags what still needs confirmation.**

## What it does

The agent runs an explicit 4-step loop:

| Step | Name | What happens |
|---|---|---|
| 1 | **PERCEIVE** | Parses raw form text into a structured field list |
| 2 | **ASSESS** | Scores every field's rejection risk as red, yellow, or green |
| 3 | **DECIDE / RESOLVE** | Figures out which risky fields matter and uses applicant context to answer what it safely can |
| 4 | **ACT** | Produces a full draft, bilingual explanation, and next actions before submission |

This makes it a real agent rather than a single prompt. The system inspects the form, reasons about risk, fills in supported answers autonomously, and leaves a visible trace of assumptions and unresolved fields.

## Setup

```bash
git clone <this-repo>
cd bureau-copilot
pip install -r requirements.txt
export OPENAI_API_KEY="sk-..."
```

## Run

Autonomous draft with no profile context:

```bash
python demo.py samples/scholarship_form.txt
```

Autonomous draft with applicant context:

```bash
python demo.py samples/scholarship_form.txt samples/applicant_context.json
```

If context is incomplete, the agent still produces a safe draft and marks unresolved fields as `NEEDS USER CONFIRMATION`.

## Project layout

```text
bureau-copilot/
|-- agent/
|   `-- core.py
|-- samples/
|   |-- scholarship_form.txt
|   `-- applicant_context.json
|-- demo.py
`-- docs/
```

## Next steps

- Add OCR ingestion for photographed forms
- Add a lightweight knowledge base for recurring rejection patterns
- Add an API or WhatsApp interface for real-world use
