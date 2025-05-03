import logging
from openai import OpenAI
from pydantic import BaseModel, Field, validator
from typing import Optional, Union

from utils.safe_json_response import safe_json_loads

# Initialize OpenAI client
client = OpenAI()

# Pydantic model for validation
class ExtractedParameter(BaseModel):
    value: Union[float, str] = Field(..., description="Numerical or categorical value of the parameter")
    unit: Optional[str] = Field(None, description="Measurement unit (e.g., mg/dL, bpm) or 'unknown'")
    remark: Optional[str] = Field(None, description="Any additional comment or note")

    @validator("unit", pre=True, always=True)
    def set_default_unit(cls, v):
        if not v or not v.strip():
            logging.warning("Unit is missing or empty; setting to 'unknown'")
            return "unknown"
        return v.strip()

# Function to extract structured value using LLM
def extract_with_llm(text_chunk: str, parameter_name: str) -> ExtractedParameter:
    prompt = f"""
Given the text:

{text_chunk}

Extract value, unit, and any remark for the parameter "{parameter_name}".
Return JSON like: {{"value": ..., "unit": "...", "remark": "..."}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    raw_response = response.choices[0].message.content.strip()
    logging.info(f"Raw LLM extractor Response: {raw_response}")

    parsed_json = safe_json_loads(raw_response)

    # Validate and return structured result
    return ExtractedParameter(**parsed_json)


# import logging
#
# from openai import OpenAI
#
# from utils.safe_json_response import safe_json_loads
#
# client = OpenAI()
#
# def extract_with_llm(text_chunk: str, parameter_name: str) -> dict:
#     prompt = f"""
# Given the text:
#
# {text_chunk}
#
# Extract value, unit, and any remark for the parameter "{parameter_name}".
# Return JSON like: {{"value": ..., "unit": "...", "remark": "..."}}
# """
#     response = client.chat.completions.create(model="gpt-4o-mini",
#     messages=[{"role": "user", "content": prompt}])
#
#     raw_response = response.choices[0].message.content.strip()
#     logging.info(f"Raw LLM extractor Response: {raw_response}")
#
#     return safe_json_loads(raw_response)
