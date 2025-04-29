import logging
from openai import AsyncOpenAI

aclient = AsyncOpenAI()
from utils.safe_json_response import safe_json_loads
from .retry_utils import retry_with_backoff

async def batch_extract_section(section_text: str, parameter_list: list) -> dict:
    """
    Extract all parameters for a section in one LLM call.
    """

    prompt = f"""
You are an expert data extractor.

Given this text section:

\"\"\"
{section_text}
\"\"\"

Extract the following parameters:
{parameter_list}

Return strict JSON in this format:
{{
    "Parameter Name 1": {{"value": ..., "unit": "...", "remark": "..."}},
    "Parameter Name 2": {{"value": ..., "unit": "...", "remark": "..."}},
    ...
}}

Only return the JSON object, no explanation text.
If a parameter is not found, set "value": null, "unit": "", "remark": "not found".
"""

    async def call_openai():
        response = await aclient.chat.completions.create(model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}])
        raw_response = response.choices[0].message.content.strip()
        logging.info(f"Raw Batch LLM Response: {raw_response}")
        return safe_json_loads(raw_response)

    extracted_params = await retry_with_backoff(call_openai)
    return extracted_params

