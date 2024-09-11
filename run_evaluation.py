#! /usr/bin/env python
import logging
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain.globals import set_verbose
from tqdm import tqdm

from basic.basic import get_dual_prompt
from decompose import single_decompose
from helpers import init_model, read_all_cases

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Suppress some loggers
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langchain").setLevel(logging.WARNING)
set_verbose(False)

# Load azure credentials
load_dotenv()

# Setup paths
project_folder = Path(os.getcwd())
output_folder = project_folder / "data" / "output" / "Orthopaedics"
case_dir = project_folder / "data" / 'processed'

llm, model_id = init_model("gpt-4-turbo", temperature=0.0)

if not case_dir.exists():
    raise FileNotFoundError(f"Cases directory not found at {case_dir}")

if not output_folder.exists():
    output_folder.mkdir(parents=True)

case_dict = read_all_cases(base_dir=case_dir,
                           filter_specialty='Orthopaedics',
                           filter_language='Swedish')


def save_output(dest: Path, file_name: str, out_str: str):
    """
    Save the output string to a file.
    """
    # The output is delimited by the tags <discharge_summary> and </discharge_summary>
    # We will remove these tags and save the output to a file
    out_str = out_str.replace("<discharge_summary>",
                              "").replace("</discharge_summary>", "")
    with open(dest / file_name, "w", encoding="utf-8") as f:
        f.write(out_str)


start_time: float | None = None

# Use tqdm to create a progress bar
for case in tqdm(case_dict.values(), desc="Processing cases"):
    logging.info("Processing case %s...", case.case_id)

    # Pause until a minute has passed since the last request
    if start_time is not None:
        elapsed_time = time.time() - start_time
        if elapsed_time < 60:
            time.sleep(60 - elapsed_time)

    # Update the start time
    start_time = time.time()

    try:
        basic_out_str = get_dual_prompt(
            llm=llm,
            language=case.object.language,
        ).invoke({"notes": case.text})
        decompose_out_str = single_decompose(case=case.object, llm=llm)

        prefix = f'{case.case_id}@{case.language}@${model_id}'
        save_output(output_folder, f"{prefix}@basic.txt", basic_out_str)
        save_output(output_folder, f"{prefix}@decompose.txt",
                    decompose_out_str)

        logging.info("Saved outputs for case %s", case.case_id)
    except Exception as e:
        logging.error("Error processing case %s: %s", case.case_id, str(e))

logging.info("Processing complete.")
