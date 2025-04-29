import os
import json
import logging
import asyncio
import re
from datetime import datetime
from utils.safe_json_response import safe_json_loads
from phase1_semantic.parameter_detector import detect_parameters
from phase2_extraction.llm_batch_extractor import batch_extract_section
from models.master_parameter_list import MASTER_PARAMETERS, SECTION_MAPPING


# ----------------------------------------
# Constants and config
# ----------------------------------------

SECTION_NAMES = list(set(SECTION_MAPPING.values()))

# ----------------------------------------
# Main pipeline
# ----------------------------------------
def load_pdf_text(pdf_path: str) -> str:
    from langchain_community.document_loaders import PyPDFLoader
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    return "\n".join(doc.page_content for doc in docs)

def save_output_json(output_dir: str, final_result: dict, base_name: str):
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(output_dir, f"{base_name}_{timestamp}.json")
    with open(output_path, "w") as f:
        json.dump(final_result, f, indent=4)
    logging.info(f"Saved result to {output_path}")

def split_text_into_sections(full_text: str, section_names: list[str]) -> dict[str, str]:
    section_pattern = r"(?P<heading>{})".format("|".join(map(re.escape, section_names)))
    matches = list(re.finditer(section_pattern, full_text, re.IGNORECASE))
    section_text_map = {}
    for i, match in enumerate(matches):
        section_name = match.group("heading").strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        section_body = full_text[start:end].strip()
        section_text_map[section_name] = section_body
    return section_text_map


def group_parameters_by_section(detection_result, section_mapping):
    section_to_params = {}
    for param_info in detection_result:
        parameter = param_info["parameter"]
        if not param_info.get("found"):
            continue
        section = section_mapping.get(parameter)
        if not section:
            continue
        section_to_params.setdefault(section, []).append(parameter)
    return section_to_params

def build_section_text_param_map(full_text: str, detection_result, section_mapping, section_names):
    section_to_parameters = group_parameters_by_section(detection_result, section_mapping)
    section_to_text = split_text_into_sections(full_text, section_names)
    section_to_text_and_parameters = {}
    for section_name, param_list in section_to_parameters.items():
        section_text = section_to_text.get(section_name)
        if section_text:
            section_to_text_and_parameters[section_name] = (section_text, param_list)
        else:
            logging.warning(f"Section text not found for: {section_name}")
    return section_to_text_and_parameters


def main(pdf_path: str, output_dir: str):
    logging.basicConfig(level=logging.INFO)

    # Step 1: Load PDF
    full_text = load_pdf_text(pdf_path)
    logging.info(f"Loaded PDF: {pdf_path}")

    # Step 2: Detect parameters
    detection_result = detect_parameters(full_text, MASTER_PARAMETERS)
    logging.info(f"Parameters detected: {[(r['parameter'], r['found']) for r in detection_result]}")

    # Step 3: Build section-to-(text, parameters)
    section_to_text_and_parameters = build_section_text_param_map(full_text, detection_result, SECTION_MAPPING, SECTION_NAMES)

    # Step 4: Async batch extraction
    async def run_extraction():
        tasks = []
        for section, (text, param_list) in section_to_text_and_parameters.items():
            logging.info(f"Extracting section: {section} | Params: {param_list}")
            tasks.append(batch_extract_section(text, param_list))
        return await asyncio.gather(*tasks)

    section_outputs = asyncio.run(run_extraction())

    # Step 5: Merge all section results
    final_result = {}
    for section_result in section_outputs:
        final_result.update(section_result)

    # Step 6: Save output
    # base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    # save_output_json(output_dir, final_result, base_name)
    return final_result

# ----------------------------------------
# Entry point
# ----------------------------------------
if __name__ == "__main__":
    pdf_path = "/Users/spatkar/PycharmProjects/Health_Tracker_Python/pdfs/Shashank Patkar Report 28052022.pdf"  # <-- Update this
    output_dir = "medical_extractor_project/Result_bucket2"
    main(pdf_path, output_dir)
