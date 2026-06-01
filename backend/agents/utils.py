import json
import re


def extract_json(text: str) -> dict:
    """
    Extract the first valid JSON object from LLM output.
    Handles markdown code fences (```json...```) and leading/trailing prose.
    """
    # Strip markdown fences
    text = re.sub(r"```(?:json)?\s*", "", text).strip()
    text = text.replace("```", "").strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find first {...} block
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in response")

    # Walk through finding balanced braces
    depth = 0
    end = start
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break

    candidate = text[start : end + 1]

    # Attempt to fix common truncation: add closing braces/brackets
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # Try to auto-close truncated JSON
        fixed = _auto_close(candidate)
        return json.loads(fixed)


def _auto_close(s: str) -> str:
    """Add missing closing braces/brackets to truncated JSON."""
    stack = []
    in_string = False
    escape = False
    for ch in s:
        if escape:
            escape = False
            continue
        if ch == "\\" and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
        if not in_string:
            if ch in "{[":
                stack.append("}" if ch == "{" else "]")
            elif ch in "}]":
                if stack:
                    stack.pop()
    return s + "".join(reversed(stack))
