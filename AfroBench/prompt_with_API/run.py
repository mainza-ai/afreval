import os
import yaml
import glob
import logging
import pandas as pd
from pathlib import Path
from main import process_task

logging.basicConfig(
    level=logging.INFO,  # Set logging level
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def run_tasks(task_files: list, model_name: str, output_dir: str, prompt_no=None,
              limit: int = None, use_fewshot=False):
    for task_file in task_files:
        try:
            # Load YAML file
            with open(task_file, 'r') as file:
                task = yaml.safe_load(file)

            task_name = task.get("name", Path(task_file).stem)
            logging.info(f"Starting task: {task_name}")

            output_dir = f"{output_dir}/{task_name}/{model_name}/"
            os.makedirs(output_dir, exist_ok=True)

            # Process task for each language
            for language in task.get("languages", []):
                # Ensure output directory exists
                output_file = os.path.join(output_dir, f"{task_name}_{language}_results.csv")

                if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                    logging.info(f"Skipping {language}, results already exist.")
                    continue

                logging.info(f"Processing language: {language}")
                process_task(task, language, model_name, output_file, prompt_no, limit)
            result_files = glob.glob(os.path.join(output_dir, f"{task_name}_*_results.csv"))
            combined_df = pd.concat([pd.read_csv(file) for file in result_files], ignore_index=True)
            combined_df.to_csv(os.path.join(output_dir, f"{task_name}_combined_results.csv"), index=False)
        except Exception as e:
            logging.info(f"Error in processing task '{task_file}': {e}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run tasks from YAML configurations.")
    parser.add_argument("--tasks", nargs="+", required=True,
                        help="List of task YAML file paths or a directory containing them.")
    parser.add_argument("--model", type=str, required=True, help="Model name to use for processing.")
    parser.add_argument("--output", type=str, required=True, help="Output directory to save results.")
    parser.add_argument("--limit", type=int, help="Useful for testing a small number of samples")
    parser.add_argument("--prompt_no", type=int, help="Specific prompt number to run (1-based index).")
    parser.add_argument("--use_fewshot", type=bool, help="Specifies whether or not to run fewshot evaluation.")
    args = parser.parse_args()

    # Resolve task files
    task_files = []
    for task_path in args.tasks:
        if os.path.isfile(task_path):
            task_files.append(task_path)
        elif os.path.isdir(task_path):
            task_files.extend([str(p) for p in Path(task_path).glob("*.yaml")])
        else:
            logging.info(f"Invalid task path: {task_path}")

    if not task_files:
        logging.info("No valid task files found.")
        return

    # Run tasks
    run_tasks(task_files, args.model, args.output, args.prompt_no, args.limit, args.use_fewshot)


if __name__ == "__main__":
    main()
