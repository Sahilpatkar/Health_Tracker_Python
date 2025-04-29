def build_detection_prompt(text: str, master_list: list) -> str:
    return f"""
You are an expert medical report reader.
Given the following text:

{text}

Find if any of the following parameters exist: {', '.join(master_list)}.

Use semantic understanding, approximate match is allowed.
Return JSON: [{{"parameter": "<name>", "found": true/false, "location_hint": "<optional>"}}]
"""