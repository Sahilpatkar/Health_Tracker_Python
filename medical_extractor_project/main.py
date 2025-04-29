

from loader.pdf_loader import load_pdf_text
from phase1_semantic.parameter_detector import detect_parameters
from phase2_extraction.regex_extractor import extract_with_regex
from phase2_extraction.llm_extractor import extract_with_llm
from models.master_parameter_list import MASTER_PARAMETERS
from utils.filename_generator import generate_output_filename
from utils.logger import setup_logger
import logging

from utils.per_report_logger import setup_report_logger
from utils.text_chunker import split_text_into_chunks
from utils.token_estimator import pretty_print_estimate


def report_parameters_extractor(input_pdf_path: str, output_json_path: str):
    setup_logger()

    #Load PDF text
    logging.info(f"Loading PDF: {input_pdf_path}")
    full_text = load_pdf_text(input_pdf_path)

    input_tokens, est_cost = pretty_print_estimate(full_text)

    # Decide smart path
    if input_tokens < 100_000:
        # Small file, full text detection
        detection_result = detect_parameters(full_text, MASTER_PARAMETERS)
    else:
        # Big file, split smartly
        logging.warning(f"Large file detected ({input_tokens} tokens), applying smart chunking...")

        chunks = split_text_into_chunks(full_text)

        logging.info(f"Split text into {len(chunks)} chunks for detection.")

        # Detect parameters across all chunks
        detection_result = {}
        for idx, chunk in enumerate(chunks):
            logging.info(f"Running detection on chunk {idx + 1}/{len(chunks)}")
            partial_result = detect_parameters(chunk, MASTER_PARAMETERS)

            # Merge results
            for param, info in partial_result.items():
                if param not in detection_result:
                    detection_result[param] = info
                else:
                    # If any chunk finds it, mark found
                    detection_result[param]["found"] = detection_result[param]["found"] or info["found"]

        logging.info("Finished chunked detection.")

    logging.info(f"Parameters detected: {[(k, v['found']) for k, v in detection_result.items()]}")

    #Extract values
    final_result = {}

    for parameter, info in detection_result.items():
        if not info['found']:
            continue

        text_chunk = full_text

        #Try regex first
        value, unit, remark = extract_with_regex(text_chunk, parameter)

        if value is None:
            # Fallback to LLM extraction
            logging.info(f"Regex failed for {parameter}, trying LLM extraction.")
            extracted = extract_with_llm(text_chunk, parameter)
            value = extracted.get("value")
            unit = extracted.get("unit")
            remark = extracted.get("remark")

        final_result[parameter] = {
            "value": value,
            "unit": unit,
            "remark": remark
        }

    # def group_parameters_by_section(detection_result, section_mapping):
    #     """
    #     Given detection results and parameter-to-section mapping,
    #     returns {section_name: [list_of_parameters]}
    #     """
    #     section_to_params = {}
    #
    #     for param_info in detection_result:
    #         parameter = param_info["parameter"]
    #         found = param_info["found"]
    #
    #         if not found:
    #             continue
    #
    #         # Find section this parameter belongs to
    #         section = section_mapping.get(parameter)
    #         if not section:
    #             continue  # Skip if unknown section
    #
    #         if section not in section_to_params:
    #             section_to_params[section] = []
    #         section_to_params[section].append(parameter)
    #
    #     return section_to_params


    # 4. Save output
    #output_json_path = generate_output_filename(input_pdf_path, output_dir="medical_extractor_project/Result_bucket")

    # Create per-report logger
    #log_file_path = output_json_path.replace(".json", ".log")
    #report_logger = setup_report_logger(log_file_path)

    # Now inside your main() — use report_logger instead of global logging
    #report_logger.info(f"Processing report: {input_pdf_path}")
    #report_logger.info(f"Saving outputs to: {output_json_path}")

    # When estimating tokens
    #input_tokens, est_cost = pretty_print_estimate(full_text)

    # Log section detection
    #report_logger.info(f"detection_result: {detection_result.items()}")
    #report_logger.info(f"Sections missing: {sections_missing}")

    # After detection
    #report_logger.info(f"Detected {len(parameters_detected)} parameters.")

    # If errors occur


    # Now your save logic remains the same
    # processed_dir_name = os.path.dirname(output_json_path)
    # os.makedirs(processed_dir_name, exist_ok=True)
    #
    # with open(output_json_path, "w") as f:
    #     json.dump(final_result, f, indent=4)
    #
    # logging.info(f"Extraction complete! Output saved to {processed_dir_name}")
    return final_result

if __name__ == "__main__":
    import sys

    pdf_path = "/Users/spatkar/PycharmProjects/Health_Tracker_Python/pdfs/Shashank Patkar Report 28052022.pdf"#sys.argv[1]
    output_json_path = "Result_bucket/extracted_results.json"
    report_parameters_extractor(pdf_path, output_json_path)
