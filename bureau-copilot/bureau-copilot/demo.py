"""
Bureaucracy Copilot - CLI Demo
==============================

Autonomous usage:
    python demo.py samples/scholarship_form.txt

With applicant context:
    python demo.py samples/scholarship_form.txt applicant_context.json
"""

import json
import os
import sys
from typing import Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.core import decide_questions, run_autonomous

RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"

COLOR = {"red": RED, "yellow": YELLOW, "green": GREEN}


def banner(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}{text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")


def load_context(path: str) -> Dict[str, str]:
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("Context JSON must be an object of key/value pairs.")
    return {str(key): str(value) for key, value in data.items()}


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python demo.py <path_to_form_text_file> [applicant_context.json]")
        sys.exit(1)

    form_path = sys.argv[1]
    context = {}

    if len(sys.argv) >= 3:
        context = load_context(sys.argv[2])

    with open(form_path, "r", encoding="utf-8") as handle:
        raw_text = handle.read()

    banner("AUTONOMOUS AGENT RUN")
    print("Reading the form, assessing rejection risk, resolving what it can, and drafting safely.\n")
    state = run_autonomous(raw_text, user_context=context)

    print(f"{BOLD}Fields found:{RESET} {', '.join(state.fields)}\n")
    print(f"{BOLD}Risk assessment:{RESET}")
    for assessment in state.assessments:
        color = COLOR.get(assessment.risk, "")
        print(f"  {color}[{assessment.risk.upper():6s}]{RESET} {assessment.field_name:25s} - {assessment.reason}")

    risky = decide_questions(state)
    if risky:
        banner("RISKY FIELDS THE AGENT INSPECTED")
        for item in risky:
            color = COLOR.get(item.risk, "")
            print(f"  {color}- {item.field_name}{RESET}: {item.clarifying_question}")
        print()

    if state.user_answers:
        banner("AUTONOMOUSLY RESOLVED ANSWERS")
        for key, value in state.user_answers.items():
            print(f"  - {key}: {value}")
        print()

    if state.unresolved_questions:
        banner("STILL NEEDS CONFIRMATION")
        for item in state.unresolved_questions:
            print(f"  - {item}")
        print()

    if state.assumptions:
        banner("SAFE ASSUMPTIONS / PLACEHOLDERS")
        for item in state.assumptions:
            print(f"  - {item}")
        print()

    banner("FINAL DRAFT")
    print(f"{state.final_draft}\n")

    banner("WHY THIS MATTERS")
    print(f"{BOLD}English:{RESET}\n{state.explanation_en}\n")
    print(f"{BOLD}Telugu:{RESET}\n{state.explanation_te}\n")

    if state.follow_up_actions:
        banner("NEXT ACTIONS BEFORE SUBMISSION")
        for item in state.follow_up_actions:
            print(f"  - {item}")
        print()

    banner("AGENT TRACE")
    for item in state.execution_log:
        print(f"  - {item}")


if __name__ == "__main__":
    main()
