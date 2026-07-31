import re
import os
import logging
import random
import pandas as pd
from typing import List, Tuple, Any

from datasets import load_dataset
from filters import filter_response, decontaminate_response, format_span, extract_pos, extract_regex
from utils import get_language, call_model
from metrics import acc_all, f1_score_metric, acc_score_pos, bleu, chrf, span_f1_seqio, exact_match_fn, bertscore_fn

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


METRIC_FUNCTIONS = {
    "acc": acc_all,
    "f1": f1_score_metric,
    "acc_pos": acc_score_pos,
    "bleu": bleu,
    "chrf": chrf,
    "span_f1": span_f1_seqio,
    "exact_match": exact_match_fn,
    "bert_score": bertscore_fn
}

FILTERS = {
    "format_span": format_span,
    "extract_pos": extract_pos,
    "extract_regex": extract_regex
}


def evaluate_task(items: List[Tuple[Any, Any]], metric_name: str) -> float:
    metric_fn = METRIC_FUNCTIONS.get(metric_name)
    if not metric_fn:
        raise ValueError(f"Unknown metric: {metric_name}")
    return metric_fn(items)


def filter_task(responses: List[str], filter_name: str) -> float:
    filter_fn = FILTERS.get(filter_name)
    if not filter_fn:
        raise ValueError(f"Unknown metric: {filter_name}")
    return filter_fn(responses)


def validate_and_replace(filtered_responses, targets, choices):
    """Validate filtered responses and replace invalid ones."""
    valid_responses = []
    for idx, response in enumerate(filtered_responses):
        if response not in choices:
            # Replace with a choice that is not the target
            replacement = next(choice for choice in choices if choice != targets[idx])
            valid_responses.append(replacement)
        else:
            valid_responses.append(response)
    return valid_responses


def process_task(task, langcode, model_name, output_file, prompt_number=None, limit=None, use_fewshot=False):
    # Check if output file already exists
    if os.path.exists(output_file):
        existing_df = pd.read_csv(output_file)
        processed_indexes = set(zip(existing_df["prompt"], existing_df["index"]))
    else:
        existing_df = pd.DataFrame()
        processed_indexes = set()

    # Few-shot settings
    num_fewshot = task.get("num_fewshot", 5)

    # dataset parameters
    dataset_args = {"split": task["test_split"], "name": langcode}
    if task.get("name") == "uhura-arc-easy":
        dataset_args = {"split": task["test_split"], "name": f"{langcode}_multiple_choice"}
    if task.get("name") == "ntrex":
        if langcode.startswith('eng'):
            dataset_args = {"split": task["test_split"], "name": langcode.split('-')[-1]}
        else:
            dataset_args = {"split": task["test_split"], "name": langcode.split('-')[0]}
    if task.get("dataset_name") is not None:
        dataset_args = {"split": task["test_split"], "name": task["dataset_name"]}
    if task.get("trust_remote_code") is not None:
        dataset_args["trust_remote_code"] = task["trust_remote_code"]

    # load dataset
    dataset = load_dataset(task["dataset"], **dataset_args)

    if use_fewshot:
        fewshot_dataset_args = dataset_args.copy()  # Make a separate copy
        fewshot_dataset_args["split"] = task["fewshot_split"]

        fewshot_dataset = load_dataset(task["dataset"], **fewshot_dataset_args)
        print(f"Loaded {num_fewshot} few-shot examples.")
    logging.info("Dataset loaded successfully.")

    # Determine target column and source column where applicable
    target_suffix = task.get("target_suffix", "")
    target_prefix = task.get("target_prefix", "")

    source_lang, target_lang = (f"{langcode.split('-')[0]}", f"{langcode.split('-')[-1]}")

    if task['name'] == 'mafand':
        source_column = task['target']
        target_column = task['target']
        if task['reverse']:
            source_lang, target_lang = (f"{langcode.split('-')[0]}", f"{langcode.split('-')[-1]}")
        else:
            target_lang, source_lang = (f"{langcode.split('-')[0]}", f"{langcode.split('-')[-1]}")
    elif task.get("target"):
        target_column = task["target"]
        source_column = None
    elif target_suffix:
        source_column, target_column = (
            f"{langcode.split('-')[0]}_{target_suffix}",
            f"{langcode.split('-')[-1]}_{target_suffix}",
        )
    elif target_prefix:
        source_column, target_column = (
            f"{target_prefix}_{langcode.split('-')[0]}",
            f"{target_prefix}_{langcode.split('-')[-1]}",
        )
    else:
        raise ValueError("Target column could not be determined. Check task configuration.")

    # build prompts
    if prompt_number is not None:
        # Validate the prompt number
        if not (1 <= prompt_number <= len(task["prompts"])):
            logging.info(f"Invalid prompt number {prompt_number}. Skipping...")
            return
        prompts_to_run = [(prompt_number, task["prompts"][prompt_number - 1])]
    else:
        prompts_to_run = enumerate(task["prompts"], start=1)

    for prompt_idx, prompt_template in prompts_to_run:
        logging.info(f"Processing prompt {prompt_idx}...")
        prompts_with_indexes = []
        placeholders = re.findall(r"\{\{(.*?)\}\}", prompt_template)

        dataset_length = range(len(dataset)) if limit is None else range(len(dataset[:limit]))

        for idx in dataset_length:
            if (prompt_idx, idx) in processed_indexes:
                continue  # Skip already processed rows

            # Construct few-shot examples if applicable
            fewshot_prompt = ""
            if use_fewshot:
                fewshot_samples = random.sample(range(len(fewshot_dataset)), num_fewshot)
                for index in fewshot_samples:
                    temp_prompt = prompt_template
                    for placeholder in placeholders:
                        if placeholder == "source":
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", get_language(source_lang))
                        elif placeholder == "target":
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", get_language(target_lang))
                        elif placeholder == "source_column":
                            if task['name'] == 'mafand':
                                temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}",
                                                                  str(fewshot_dataset[source_column][index][source_lang]))
                            else:
                                temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}",
                                                                  str(fewshot_dataset[source_column][index]))
                        elif placeholder == "choices" and task['name'] == "afrimmlu":
                            data = eval(fewshot_dataset['choices'][index])
                            choices = "\n".join([f"{chr(65 + i)}: {opt}" for i, opt in enumerate(data)])
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", choices)
                        elif placeholder == "choices" and task['name'] == "uhura-arc-easy":
                            data = fewshot_dataset['choices'][index]
                            choices = "\n".join(
                                [f"{label}: {text}" for label, text in zip(data["label"], data["text"])])
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", choices)
                        elif placeholder == "language" and task['name'] == "xlsum":
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", langcode)
                        elif placeholder == "language":
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}", get_language(langcode))
                        elif placeholder in dataset.features:
                            temp_prompt = temp_prompt.replace(f"{{{{{placeholder}}}}}",
                                                              str(fewshot_dataset[placeholder][index]))
                    temp_prompt += f" {fewshot_dataset[target_column][index]}\n\n"
                    fewshot_prompt += temp_prompt

            # Construct final prompt
            prompt = fewshot_prompt + prompt_template
            for placeholder in placeholders:
                if placeholder == "source":
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", get_language(source_lang))
                elif placeholder == "target":
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", get_language(target_lang))
                elif placeholder == "source_column":
                    if task['name'] == 'mafand':
                        prompt = prompt.replace(f"{{{{{placeholder}}}}}", str(dataset[source_column][idx][source_lang]))
                    else:
                        prompt = prompt.replace(f"{{{{{placeholder}}}}}", str(dataset[source_column][idx]))
                elif placeholder == "choices" and task['name'] == "uhura-arc-easy":
                    data = dataset['choices'][idx]
                    choices = "\n".join([f"{label}: {text}" for label, text in zip(data["label"], data["text"])])
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", choices)
                elif placeholder == "choices" and task['name'] == "afrimmlu":
                    options = eval(dataset['choices'][idx])
                    choices = "\n".join([f"{chr(65 + i)}: {opt}" for i, opt in enumerate(options)])
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", choices)
                elif placeholder == "language" and task['name'] == "xlsum":
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", langcode)
                elif placeholder == "language":
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", get_language(langcode))
                elif placeholder in dataset.features:
                    prompt = prompt.replace(f"{{{{{placeholder}}}}}", str(dataset[placeholder][idx]))

            prompts_with_indexes.append((idx, prompt))

        if not prompts_with_indexes:
            logging.info(f"Skipping prompt {prompt_idx}, all items processed.")
            continue

        indexes, prompts = zip(*prompts_with_indexes)

        # Call the model
        raw_responses = call_model(model_name, prompts)

        # Batch decontamination
        decontaminated_responses = decontaminate_response(prompts, raw_responses)
        post_process = task.get("map_response", {})

        # Batch filtering
        if 'choices' in task:
            if 'verbalizer' in task:
                filtered_responses = filter_response(decontaminated_responses, task["choices"], task["verbalizer"])
            else:
                filtered_responses = filter_response(decontaminated_responses, task["choices"])

            filtered_responses = validate_and_replace(filtered_responses, dataset[target_column], task["choices"])
        elif 'filters' in task:
            filtered_responses = decontaminated_responses
            for filter_config in task["filters"]:
                filtered_responses = filter_task(filtered_responses, filter_config)
        else:
            filtered_responses = decontaminated_responses

        results = [
            {
                "index": idx,
                "prompt_no": prompt_idx,
                "prompt": prompt,
                "target": dataset[target_column][idx][target_lang] if task['name'] == 'mafand' else dataset[target_column][idx],
                "raw_output": raw_response,
                "filtered_output": post_process[filtered_responses] if post_process else filtered_responses,
            }
            for idx, prompt, raw_response, filtered_responses in zip(
                indexes, prompts, raw_responses, filtered_responses
            )
        ]

        for metric_name in task["metrics"]:
            for result in results:
                try:
                    evaluation_items = [(result["target"].lower(), result["filtered_output"].lower())]
                except AttributeError:
                    evaluation_items = [(result["target"], result["filtered_output"])]
                result[metric_name] = evaluate_task(evaluation_items, metric_name)

        # Convert results to DataFrame and save scores
        new_df = pd.DataFrame(results)
        updated_df = pd.concat([existing_df, new_df], ignore_index=True)
        updated_df.to_csv(output_file, index=False)
        logging.info(f"Results for prompt {prompt_idx} saved to {output_file}.")
        existing_df = updated_df  # Update checkpoint

        # Compute average scores for the prompt
        avg_score = {"language": langcode, "prompt": f"prompt_{prompt_idx}"}
        for metric_name in task["metrics"]:
            avg_score[metric_name] = new_df[metric_name].mean()

        # Convert to DataFrame for current iteration
        current_avg_scores_df = pd.DataFrame([avg_score])

        # Output file for average scores
        avg_output_file = os.path.join(os.path.dirname(output_file), f"{task['name']}_results.csv")
        if os.path.exists(avg_output_file):
            existing_avg_scores_df = pd.read_csv(avg_output_file)
            updated_avg_scores_df = pd.concat([existing_avg_scores_df, current_avg_scores_df], ignore_index=True)
        else:
            updated_avg_scores_df = current_avg_scores_df

        # Save the updated DataFrame
        updated_avg_scores_df.to_csv(avg_output_file, index=False)
        logging.info(f"Average scores for prompt {prompt_idx} saved to {avg_output_file}.")
