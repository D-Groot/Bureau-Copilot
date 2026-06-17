"""
Bureaucracy Copilot - Agent Core
================================

This module implements an explicit agent loop for high-risk bureaucratic
forms. The loop is designed to be inspectable and autonomous:

1. PERCEIVE         Parse raw form text into structured field names.
2. ASSESS           Score rejection risk for each field.
3. DECIDE/RESOLVE   Use applicant context to answer risky questions when
                    possible and isolate what still needs confirmation.
4. ACT              Produce a field-by-field draft and bilingual guidance.
"""

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from openai import OpenAI

MODEL = os.environ.get("BUREAU_MODEL", "gpt-4o-mini")
MAX_JSON_REPAIR_ATTEMPTS = 2


def _client() -> OpenAI:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set OPENAI_API_KEY in your environment before running the agent."
        )
    return OpenAI(api_key=api_key)


@dataclass
class FieldAssessment:
    field_name: str
    risk: str  # "red" | "yellow" | "green"
    reason: str
    clarifying_question: Optional[str] = None


@dataclass
class AgentState:
    raw_form_text: str
    fields: List[str] = field(default_factory=list)
    assessments: List[FieldAssessment] = field(default_factory=list)
    user_context: Dict[str, str] = field(default_factory=dict)
    user_answers: Dict[str, str] = field(default_factory=dict)
    unresolved_questions: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    follow_up_actions: List[str] = field(default_factory=list)
    execution_log: List[str] = field(default_factory=list)
    final_draft: Optional[str] = None
    explanation_en: Optional[str] = None
    explanation_te: Optional[str] = None


def _strip_code_fences(text: str) -> str:
    return text.removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def _normalize_risk(value: str) -> str:
    risk = (value or "").strip().lower()
    return risk if risk in {"red", "yellow", "green"} else "yellow"


def _context_block(data: Dict[str, str]) -> str:
    if not data:
        return "(none provided)"
    return "\n".join(f"- {key}: {value}" for key, value in data.items())


def _log(state: AgentState, message: str) -> None:
    state.execution_log.append(message)


def _request_json(
    *,
    client: OpenAI,
    prompt: str,
    schema_hint: str,
    temperature: float = 0,
) -> Dict[str, Any]:
    messages = [{"role": "user", "content": prompt}]

    for _ in range(MAX_JSON_REPAIR_ATTEMPTS + 1):
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temperature,
        )
        raw = _strip_code_fences(resp.choices[0].message.content or "")
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            messages.extend(
                [
                    {"role": "assistant", "content": raw},
                    {
                        "role": "user",
                        "content": (
                            "Return only valid JSON with no markdown fences. "
                            f"Match this shape exactly: {schema_hint}"
                        ),
                    },
                ]
            )

    raise ValueError("Model did not return valid JSON after repair attempts.")


def perceive(state: AgentState) -> AgentState:
    client = _client()
    prompt = f"""You are reading a raw government/institutional form that may
be messy, OCR'd, or copy-pasted. Extract only the list of field names a
person must fill in.

Return strict JSON:
{{"fields": ["field1", "field2", "..."]}}

No commentary. No markdown fences.

FORM TEXT:
---
{state.raw_form_text}
---
"""
    data = _request_json(
        client=client,
        prompt=prompt,
        schema_hint='{"fields": ["Full Name", "Date of Birth"]}',
    )
    state.fields = [str(item).strip() for item in data.get("fields", []) if str(item).strip()]
    _log(state, f"Perceived {len(state.fields)} fields.")
    return state


def assess(state: AgentState) -> AgentState:
    client = _client()
    prompt = f"""You are a careful bureaucratic-forms expert in India. For each
field below, assess the risk that a person fills it incorrectly and gets
silently rejected or disqualified later.

Rules:
- "red" = high risk of silent rejection
- "yellow" = moderate risk or ambiguous wording
- "green" = low risk and self-explanatory

For every red or yellow field, write one short, specific clarifying question
about the applicant's situation.

Fields: {json.dumps(state.fields)}

Return strict JSON:
{{
  "assessments": [
    {{
      "field_name": "...",
      "risk": "red|yellow|green",
      "reason": "...",
      "clarifying_question": "... or null"
    }}
  ]
}}
"""
    data = _request_json(
        client=client,
        prompt=prompt,
        schema_hint=(
            '{"assessments": [{"field_name": "Category", "risk": "red", '
            '"reason": "Eligibility-linked field.", '
            '"clarifying_question": "Which category is listed on your certificate?"}]}'
        ),
    )

    assessments: List[FieldAssessment] = []
    for item in data.get("assessments", []):
        field_name = str(item.get("field_name", "")).strip()
        if not field_name:
            continue
        assessments.append(
            FieldAssessment(
                field_name=field_name,
                risk=_normalize_risk(item.get("risk", "")),
                reason=str(item.get("reason", "")).strip() or "Potential rejection risk.",
                clarifying_question=(
                    str(item.get("clarifying_question", "")).strip() or None
                ),
            )
        )

    state.assessments = assessments
    _log(state, f"Assessed {len(state.assessments)} fields.")
    return state


def decide_questions(state: AgentState) -> List[FieldAssessment]:
    return [
        item
        for item in state.assessments
        if item.risk in ("red", "yellow") and item.clarifying_question
    ]


def resolve_questions(state: AgentState) -> AgentState:
    client = _client()
    risky_questions = decide_questions(state)
    if not risky_questions:
        _log(state, "No risky fields needed follow-up.")
        return state

    prompt = f"""You are an autonomous form-completion agent.

Use the applicant context to answer risky questions when the answer is
supported. If the answer is uncertain, leave it unresolved instead of
inventing personal facts.

Risky questions:
{json.dumps([asdict(item) for item in risky_questions], ensure_ascii=False)}

Applicant context:
{_context_block(state.user_context)}

Return strict JSON:
{{
  "resolved_answers": {{"field name": "best supported answer"}},
  "unresolved_questions": ["field names still needing user confirmation"],
  "assumptions": ["short note for each cautious assumption or placeholder"]
}}
"""
    data = _request_json(
        client=client,
        prompt=prompt,
        schema_hint=(
            '{"resolved_answers": {"Domicile State": "Telangana"}, '
            '"unresolved_questions": ["Annual Family Income"], '
            '"assumptions": ["Left income unresolved because no certificate value was provided."]}'
        ),
    )

    state.user_answers.update(
        {
            str(field).strip(): str(value).strip()
            for field, value in data.get("resolved_answers", {}).items()
            if str(field).strip() and str(value).strip()
        }
    )
    state.unresolved_questions = [
        str(item).strip()
        for item in data.get("unresolved_questions", [])
        if str(item).strip()
    ]
    state.assumptions = [
        str(item).strip() for item in data.get("assumptions", []) if str(item).strip()
    ]
    _log(
        state,
        (
            f"Resolved {len(state.user_answers)} risky answers from context; "
            f"{len(state.unresolved_questions)} remain unresolved."
        ),
    )
    return state


def act(state: AgentState) -> AgentState:
    client = _client()
    assess_block = "\n".join(
        f"- {item.field_name} [{item.risk}]: {item.reason}" for item in state.assessments
    )
    unresolved_block = (
        "\n".join(f"- {item}" for item in state.unresolved_questions)
        if state.unresolved_questions else "(none)"
    )
    assumptions_block = (
        "\n".join(f"- {item}" for item in state.assumptions)
        if state.assumptions else "(none)"
    )

    prompt = f"""You are finishing a form-filling assistance task.

Original fields:
{json.dumps(state.fields)}

Risk assessment so far:
{assess_block}

Resolved answers from applicant context:
{_context_block(state.user_answers)}

Unresolved fields:
{unresolved_block}

Assumptions already made:
{assumptions_block}

Return strict JSON:
{{
  "draft": "...",
  "explanation_en": "...",
  "explanation_te": "...",
  "follow_up_actions": ["..."]
}}

Rules:
- The draft must cover every field.
- For unresolved fields, clearly mark "NEEDS USER CONFIRMATION".
- Use safe guidance, not invented exact personal data.
- explanation_en must stay under 120 words.
- explanation_te must be natural Telugu script.
- follow_up_actions should be short, practical, and submission-focused.
"""
    data = _request_json(
        client=client,
        prompt=prompt,
        schema_hint=(
            '{"draft": "...", "explanation_en": "...", "explanation_te": "...", '
            '"follow_up_actions": ["Verify income certificate amount."]}'
        ),
        temperature=0.2,
    )

    state.final_draft = str(data.get("draft", "")).strip()
    state.explanation_en = str(data.get("explanation_en", "")).strip()
    state.explanation_te = str(data.get("explanation_te", "")).strip()
    state.follow_up_actions = [
        str(item).strip() for item in data.get("follow_up_actions", []) if str(item).strip()
    ]
    _log(state, "Produced final draft and bilingual explanation.")
    return state


def run_perceive_and_assess(raw_form_text: str) -> AgentState:
    state = AgentState(raw_form_text=raw_form_text)
    state = perceive(state)
    state = assess(state)
    return state


def run_act(state: AgentState, user_answers: Dict[str, str]) -> AgentState:
    state.user_answers = user_answers
    state = act(state)
    return state


def run_autonomous(
    raw_form_text: str,
    user_context: Optional[Dict[str, str]] = None,
) -> AgentState:
    state = AgentState(
        raw_form_text=raw_form_text,
        user_context=user_context or {},
    )
    state = perceive(state)
    state = assess(state)
    state = resolve_questions(state)
    state = act(state)
    return state
