import re

def extract_with_regex(text: str, parameter_name: str):
    """
    Extracts numeric value and unit for a parameter from text using regex.
    Supports numbers with commas like 6,800.0 or 1,234
    """
    # Match: parameter name → skip non-numbers → capture number with optional commas + optional decimal → optional unit
    pattern = re.compile(
        rf"{re.escape(parameter_name)}[^\d]*(\d[\d,]*\.?\d*)[\s]*([a-zA-Zµ/%^\d]*)",
        re.IGNORECASE
    )
    match = pattern.search(text)
    if match:
        raw_value = match.group(1).replace(",", "")  # Remove commas from number
        try:
            value = float(raw_value)
        except ValueError:
            value = None
        unit = match.group(2).strip()
        return value, unit, ""
    return None, None, None
