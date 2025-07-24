import asyncio
import json
import os
from typing import Union, Optional

from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic import BaseModel, field_validator
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()

# Environment Variables
os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Health Monitoring"

# List of required parameters
REQUIRED_PARAMETERS = [
    "Hemoglobin (Hb)",
    "Total Leucocytes (WBC) count",
    "Platelet count",
    "Red blood cell (RBC) count",
    "PCV (Packed Cell Volume)",
    "MCV (Mean Corpuscular Volume)",
    "MCH (Mean Corpuscular Hb)",
    "Cholesterol (Total)",
    "Triglycerides",
    "HDL Cholesterol",
    "LDL Cholesterol",
    "VLDL Cholesterol",
    "Cholesterol/HDL Ratio",
    "LDL/HDL Ratio",
    "Apolipoprotein A1",
    "Apolipoprotein B",
    "ApoB/A1 Ratio",
    "Protein (Total)",
    "Globulin",
    "Glycated Hemoglobin (HbA1C)",
    "MPV (Mean Platelet Volume)",
    "Urea",
    "BUN (Blood Urea Nitrogen)",
    "25-OH Vitamin D",
    "TSH (Ultrasensitive)",
    "PSA",
    "ESR (Erythrocyte Sedimentation Rate)",
    "RBCs",
    "Urine Appearance",
    "Urine Colour",
    "Plasma Glucose",
    "Creatinine",
    "Uric Acid",
    "Calcium",
    "Calcium, serum",
    "HbA1c",
]

# Field mappings
FIELD_MAPPING = {
    "Apolipoprotein A1": "ApoA1",
    "Apolipoprotein B": "ApoB",
    "HbA1c": "Glycated Hemoglobin (HbA1C)",
    "Calcium, serum": "Calcium"
}

class ReportParameter(BaseModel):
    name: str
    value: Union[float, str, None]
    unit: Optional[str] = None
    remark: Optional[str] = None

    @field_validator("value")
    def parse_value(cls, v):
        if isinstance(v, (float, int)):
            return float(v)
        if isinstance(v, str):
            try:
                return float(v)
            except ValueError:
                return v
        return v

def normalize_field_name(field_name: str) -> str:
    return FIELD_MAPPING.get(field_name, field_name)

TEXTUAL_FIELDS = [
    "Colour",
    "Appearance",
    "RBCs",
    "Pus cells",
    "Epithelial cells",
    "Casts",
    "Crystals",
]

def clean_value(v, field_name=None):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if field_name in TEXTUAL_FIELDS:
            return v  # textual field, preserve as is
        try:
            return float(v.replace('<', '').replace('>', '').split('-')[0].strip())
        except:
            return None
    return None

@traceable
async def extract_from_pdf(pdf_path: str):
    model = GroqModel("llama-3.3-70b-versatile")

    required_params_string = ', '.join([f'"{param}"' for param in REQUIRED_PARAMETERS])

    batch_system_prompt = (
        f"From the health report text, strictly extract _only_ the following parameters: {required_params_string}. "
        "Return an exact JSON array like `[{\"name\":\"parameter_name\",\"unit\":\"unit\",\"value\":value,\"remark\":\"optional\"}, ...]`. "
        "If a parameter is not found, set \"value\": null, \"unit\": \"\" (empty string), and add a \"remark\": \"not found in report\". "
        "Do not invent parameters. Do not add extra text. Strict JSON output only."
    )

    batch_agent = Agent(
        "openai:gpt-4o-mini",
        system_prompt=batch_system_prompt,
        output_type=Union[list[ReportParameter], str],  # type: ignore
    )

    print("Loading PDF from:", pdf_path)
    docs = PyPDFDirectoryLoader(pdf_path).load()
    chunks = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200).split_documents(docs)

    result_dict = {}

    # Step 1: Try chunk-based batch extraction
    tasks = [batch_agent.run(chunk.page_content) for chunk in chunks]
    all_responses = await asyncio.gather(*tasks)

    for response in all_responses:
        if isinstance(response.output, list):
            for p in response.output:
                print(p)
                try:
                    field_name = normalize_field_name(p.name)
                    if field_name not in result_dict or (result_dict[field_name]["value"] is None):
                        result_dict[field_name] = {
                            "value": clean_value(p.value),
                            "unit": p.unit or "",
                            "remark": p.remark
                        }
                except Exception as e:
                    print("Error parsing parameter:", e)

    # Step 2: Check missing parameters
    missing_params = [param for param in REQUIRED_PARAMETERS if param not in result_dict]
    missing_percentage = len(missing_params) / len(REQUIRED_PARAMETERS)

    if missing_percentage > 0.3:
        print(f"High missing rate detected ({missing_percentage*100:.1f}%). Retrying with full document field-by-field...")

        # Merge full document
        full_text = "\n".join(chunk.page_content for chunk in chunks)

        # Step 3: Field-by-field extraction fallback
        tasks = [extract_single_parameter(full_text, param) for param in REQUIRED_PARAMETERS]
        all_field_results = await asyncio.gather(*tasks)

        for param, field_result in zip(REQUIRED_PARAMETERS, all_field_results):
            final_field = normalize_field_name(param)
            # Only update missing fields
            if (final_field not in result_dict) or (result_dict[final_field]["value"] is None) or (result_dict[final_field]["unit"] == ""):
                result_dict[final_field] = {
                    "value": clean_value(field_result.get("value")),
                    "unit": field_result.get("unit", ""),
                    "remark": field_result.get("remark", None) if "remark" in field_result else None
                }

    # Step 4: Final fill of missing parameters
    for param in REQUIRED_PARAMETERS:
        final_field = normalize_field_name(param)
        if final_field not in result_dict:
            result_dict[final_field] = {
                "value": None,
                "unit": "",
                "remark": "not found in report"
            }

    return result_dict

async def extract_single_parameter(full_text: str, param_name: str) -> dict:
    system_prompt = (
        f"From the following health report text, find ONLY the patient's actual measured value and unit for the parameter \"{param_name}\". "
        "Return strictly a JSON object like {\"value\":…, \"unit\":\"…\"}. "
        "Ignore any normal range, reference range, goal range, or advice text. "
        "If not found, return {\"value\": null, \"unit\": \"\"}."
    )
    agent = Agent(
        "openai:gpt-4o-mini",
        system_prompt=system_prompt,
        output_type=dict
    )

    try:
        result = await agent.run(full_text)
        return result.output
    except Exception as e:
        print(f"Error extracting {param_name}: {e}")
        return {"value": None, "unit": ""}

if __name__ == "__main__":
    results = asyncio.run(extract_from_pdf("/Users/spatkar/PycharmProjects/Health_Monitoring_project/pdfs"))
    print(json.dumps(results, indent=4))
    file_path = "ParametersResult.json"
    with open(file_path, "w") as f:
        json.dump(results, f, indent=4)
