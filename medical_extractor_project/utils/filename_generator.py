# utils/filename_generator.py

import os
from datetime import datetime

def generate_output_filename(input_pdf_path: str, output_dir: str = "Result_bucket") -> str:
    """
    Generate a smart output filename based on input PDF name and timestamp.
    Returns the full path where the output JSON should be saved.
    """
    # Get the base name of the input PDF (without extension)
    base_name = os.path.splitext(os.path.basename(input_pdf_path))[0]

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create final file name
    output_filename = f"{base_name}_{timestamp}.json"

    # Create full output path
    return os.path.join(output_dir, output_filename)
