import logging

from openai import OpenAI

from utils.safe_json_response import safe_json_loads

client = OpenAI()

def extract_with_llm(text_chunk: str, parameter_name: str) -> dict:
    prompt = f"""
Given the text:

{text_chunk}

Extract value, unit, and any remark for the parameter "{parameter_name}".
Return JSON like: {{"value": ..., "unit": "...", "remark": "..."}}
"""
    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}])

    raw_response = response.choices[0].message.content.strip()
    logging.info(f"Raw LLM extractor Response: {raw_response}")

    return safe_json_loads(raw_response)
