import asyncio
import json
import os
from typing import Union, Optional, List

from langchain_community.document_loaders import PyPDFDirectoryLoader
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
import re
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

load_dotenv()

os.environ['GROQ_API_KEY'] = os.getenv("GROQ_API_KEY")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Health Monitoring"

# --------- SECTION DEFINITIONS ---------

SECTION_PARAMETERS = {
    "Complete Blood Count": [
        "Hemoglobin (Hb)",
        "Total Leucocytes (WBC) count",
        "Platelet count",
        "Red blood cell (RBC) count",
        "PCV (Packed Cell Volume)",
        "MCV (Mean Corpuscular Volume)",
        "MCH (Mean Corpuscular Hb)",
        "MCHC (Mean Corpuscular Hb Conc.)",
        "RDW (RBC distribution width)",
        "Neutrophils",
        "Absolute Neutrophils",
        "Eosinophils",
        "Absolute Eosinophils",
        "Basophils",
        "Absolute Basophils",
        "Lymphocytes",
        "Absolute Lymphocytes",
        "Monocytes",
        "Absolute Monocytes"
    ],
    "Lipid Profile": [
        "Cholesterol (Total), serum",
        "Triglycerides, serum",
        "HDL Cholesterol, serum",
        "LDL Cholesterol, serum",
        "VLDL Cholestrol, serum",
        "Cholesterol(Total)/HDL Cholesterol Ratio",
        "LDL Cholesterol/HDL Cholesterol Ratio",
        "Apolipoprotein A1",
        "Apolipoprotein B"
    ],
    "Liver Function Test": [
        "Bilirubin-Total",
        "Bilirubin-Conjugated",
        "Bilirubin-Unconjugated",
        "SGOT (AST)",
        "SGPT (ALT)",
        "Alkaline Phosphatase",
        "Protein (total)",
        "Albumin",
        "Globulin"
    ],
    "Urine Routine Examination": [
        "Quantity Examined",
        "Appearance",
        "Colour",
        "pH",
        "R.B.Cs",
        "Pus cells",
        "Epithelial cells",
        "Casts",
        "Crystals"
    ],
    "Diabetes Markers": [
        "Glycated Hemoglobin (HbA1C)",
        "Diabetes threshold"
    ],
    "Clinical Chemistry": [
        "Gamma Glutamyl Transferase (GGT)",
        "Plasma Glucose",
        "Urea",
        "BUN",
        "Creatinine",
        "Uric Acid",
        "Calcium, serum",
        "Free T3",
        "Free T4",
        "TSH",
        "Insulin Fasting",
        "Vitamin B12",
        "25 - OH Vitamin D"
    ]
}

SECTION_ALIASES = {
    "CBC": "Complete Blood Count",
    "COMPLETE BLOOD COUNT": "Complete Blood Count",
    "HAEMATOLOGY": "Complete Blood Count",
    "HEMATOLOGY": "Complete Blood Count",
    "LIPID PROFILE": "Lipid Profile",
    "LIPID PROFILE MAXI": "Lipid Profile",
    "BIOCHEMISTRY": "Clinical Chemistry",
    "CLINICAL CHEMISTRY": "Clinical Chemistry",
    "LIVER FUNCTION TEST": "Liver Function Test",
    "URINE ROUTINE EXAMINATION": "Urine Routine Examination",
    "DIABETES": "Diabetes Markers"
}

TEXTUAL_FIELDS = [
    "Appearance",
    "Colour",
    "R.B.Cs",
    "Pus cells",
    "Epithelial cells",
    "Casts",
    "Crystals"
]

# --------- HELPERS ---------

class ReportParameter(BaseModel):
    name: str
    value: Union[float, str, None]
    unit: Optional[str] = ""
    remark: Optional[str] = ""

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

def clean_value(v, field_name=None):
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        v = v.strip()
        if field_name in TEXTUAL_FIELDS:
            return v
        try:
            return float(v.replace('<', '').replace('>', '').split('-')[0].strip())
        except:
            return None
    return None

def clean_text(text: str) -> str:
    lines = text.split("\n")
    useful_lines = []
    for line in lines:
        if re.search(r"(reference|collection date|tel|pid|sid)", line, re.I):
            continue
        useful_lines.append(line)
    return "\n".join(useful_lines)

def normalize_section(line: str) -> Optional[str]:
    """
    Normalize section header if possible using fuzzy partial match
    """
    cleaned = line.strip().upper()
    for key, value in SECTION_ALIASES.items():
        if key in cleaned:
            return value
    return None

def split_by_section(text: str) -> List[dict]:
    sections = []
    current_section = "General"
    current_text = ""

    found_sections = []

    for line in text.split("\n"):
        line = line.strip()
        normalized = normalize_section(line)
        if normalized:
            found_sections.append(normalized)
            if current_text:
                sections.append({"section": current_section, "text": current_text})
            current_section = normalized
            current_text = ""
        else:
            current_text += line + "\n"

    if current_text:
        sections.append({"section": current_section, "text": current_text})

    # Log found sections
    logging.info(f"Sections detected in document: {set(found_sections)}")

    expected_sections = set(SECTION_PARAMETERS.keys())
    missing_sections = expected_sections - set(found_sections)

    logging.info(f"Sections missing (not found in document): {missing_sections}")

    return sections

# --------- EXTRACTION ---------

async def extract_parameters(agent, section_name, section_text, required_fields):
    logging.info(f"Extracting Section: {section_name} | Fields: {required_fields}")

    full_prompt = (
        f"You are an expert medical report reader.\n\n"
        f"Section: {section_name}\n\n{section_text}\n\n"
        f"Your task is to extract ONLY these fields: {', '.join(required_fields)}.\n\n"
        "IMPORTANT RULES:\n"
        "- Approximate matching allowed. Example: 'Urea, serum by GLDH-urease' should match 'Urea'.\n"
        "- Ignore extra words like 'serum', 'by', 'method', 'calculation', etc.\n"
        "- Focus only on the main field meaning.\n"
        "- Output only the FIELD NAME as 'name', without section prefix.\n"
        "- If the field is found, extract its observed value and unit.\n"
        "- If field is not found, set 'value': null and 'remark': 'not found'.\n\n"
        "Output JSON array like:\n"
        "[\n"
        "  {\"name\": \"<field name>\", \"value\": ..., \"unit\": \"...\", \"remark\": \"...\"},\n"
        "  ...\n"
        "]"
    )

    try:
        result = await agent.run(full_prompt)
        return result.output
    except Exception as e:
        logging.error(f"Error extracting section {section_name}: {e}")
        return []


async def fallback_extract_missing(agent, full_text, missing_fields):
    results = []
    batch_size = 5
    for i in range(0, len(missing_fields), batch_size):
        batch = missing_fields[i:i + batch_size]
        logging.info(f"Fallback extracting batch: {batch}")
        fallback_prompt = (
            f"Search the full report text below and find ONLY these missing parameters: {', '.join(batch)}.\n"
            f"Return JSON array like: [{{'name':'<field name>', 'value':..., 'unit':'', 'remark':...}}].\n"
            "If not found, set 'value': null and 'remark': 'not found'.\n\n"
            f"FULL REPORT TEXT:\n{full_text}"
        )
        try:
            result = await agent.run(fallback_prompt)
            if isinstance(result.output, list):
                results.extend(result.output)
        except Exception as e:
            logging.error(f"Error extracting fallback batch {batch}: {e}")
    return results

# --------- MAIN PROCESS ---------

async def extract_from_pdf(pdf_path: str):
    model = GroqModel("llama-3.3-70b-versatile")

    agent = Agent(
        "openai:gpt-4o-mini",
        system_prompt="Extract medical parameters from health reports carefully based on instructions.",
        output_type=Union[List[ReportParameter], str],
    )

    logging.info(f"Loading PDF: {pdf_path}")
    docs = PyPDFDirectoryLoader(pdf_path).load()

    all_text = "\n".join([doc.page_content for doc in docs])
    clean_doc_text = clean_text(all_text)
    sections = split_by_section(clean_doc_text)

    result_dict = {}
    tasks = []
    all_required_fields = []

    for sec in sections:
        sec_name = sec["section"]
        sec_text = sec["text"]

        if sec_name not in SECTION_PARAMETERS:
            continue

        required_fields = SECTION_PARAMETERS[sec_name]
        all_required_fields.extend(required_fields)
        tasks.append(extract_parameters(agent, sec_name, sec_text, required_fields))

    all_section_results = await asyncio.gather(*tasks)

    for section_results in all_section_results:
        if isinstance(section_results, list):
            for p in section_results:
                print(p)
                try:
                    field_name = p.name.strip()
                    result_dict[field_name] = {
                        "value": clean_value(p.value, field_name),
                        "unit": p.unit or "",
                        "remark": p.remark or ""
                    }
                except Exception as e:
                    logging.error(f"Error parsing section parameter: {e}")

    missing_fields = [field for field in all_required_fields if not any(field in k for k in result_dict.keys())]
    logging.info(f"Missing fields after section extraction: {missing_fields}")

    if missing_fields:
        fallback_results = await fallback_extract_missing(agent, clean_doc_text, missing_fields)
        for p in fallback_results:
            try:
                field_name = p.name.strip()
                result_dict[field_name] = {
                    "value": clean_value(p.value, field_name),
                    "unit": p.unit or "",
                    "remark": p.remark or ""
                }
            except Exception as e:
                logging.error(f"Error parsing fallback parameter: {e}")

    return result_dict

# --------- ENTRY POINT ---------

if __name__ == "__main__":
    results = asyncio.run(extract_from_pdf("/Users/spatkar/PycharmProjects/Health_Monitoring_project/pdfs"))
    output_path = "FinalParametersResult.json"
    logging.info(f"Saving final output to {output_path}")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=4)
    logging.info("Process completed.")
