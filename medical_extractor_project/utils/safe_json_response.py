import json
import logging
import re

def normalize_value_field(value):
    if isinstance(value, str):
        cleaned = value.replace(',', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return value  # fallback if it's not a number string
    return value  # already numeric or null

def safe_json_loads(raw_response: str):
    """
    Clean and parse LLM JSON output even if extra explanation is present.
    Normalizes value fields with commas.
    """

    cleaned = raw_response.strip()
    print("cleaned response",cleaned)
    # Extract content inside ```json ... ``` if present
    json_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"  # match JSON inside triple backticks
    matches = re.findall(json_block_pattern, cleaned, flags=re.DOTALL)

    if matches:
        cleaned = matches[0]
    else:
        # If no block, maybe response was clean already — try fallback cleaning
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()

    try:
        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            for param, result in parsed.items():
                if isinstance(result, dict) and "value" in result:
                    result["value"] = normalize_value_field(result["value"])

        return parsed

    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse cleaned LLM output: {e}")
        raise RuntimeError(f"Invalid cleaned LLM output: {cleaned}") from e
