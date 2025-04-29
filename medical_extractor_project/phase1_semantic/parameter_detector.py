import json
import logging
import os

from phase1_semantic.prompt_templates import build_detection_prompt
from openai import OpenAI
from dotenv import load_dotenv

from utils.safe_json_response import safe_json_loads

load_dotenv()

os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Health Monitoring"
client = OpenAI()

def detect_parameters(text: str, master_list: list) -> dict:
    prompt = build_detection_prompt(text, master_list)

    response = client.chat.completions.create(model="gpt-4o-mini",
    messages=[{"role": "user", "content": prompt}])

    raw_response = response.choices[0].message.content.strip()
    logging.info(f"Raw LLM Detection Response: {raw_response}")

    detection_output = safe_json_loads(raw_response)
    return {item["parameter"]: {"found": item["found"], "hint": item.get("location_hint", "")} for item in detection_output}



