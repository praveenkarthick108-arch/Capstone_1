"""Robust JSON extraction from LLM responses that may include extra text."""
import json
import re


def extract_json(text: str) -> dict:
    """Extract first JSON object from a string, handling markdown code blocks."""
    if not text:
        return {}

    # Try direct parse first
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try extracting from markdown code block
    code_block = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
    if code_block:
        try:
            return json.loads(code_block.group(1).strip())
        except json.JSONDecodeError:
            pass

    # Find first { ... } block
    start = text.find("{")
    if start == -1:
        return {}

    # Try from the first { to end
    brace_count = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            brace_count += 1
        elif ch == "}":
            brace_count -= 1
            if brace_count == 0:
                try:
                    return json.loads(text[start: i + 1])
                except json.JSONDecodeError:
                    pass

    return {}
