# Evaluate Closed models and Open Models Using API

This script provides a simple interface for running NLP task evaluations via APIs, specifically for models 
from GPT, Gemini, and TogetherAI. You can evaluate multiple tasks across different datasets and models seamlessly.

### Model Support 
| Model Name  | API                                                             | Supported  |
|-------------|-----------------------------------------------------------------|------------|
| **GPT Models** | [openai](https://platform.openai.com/docs/quickstart?api-mode=chat) |  ✅|
| **Gemini Models** | [gemini](https://ai.google.dev/gemini-api/docs/models)          | ✅ |
| **gemma-3-27b-it**        | [gemini](https://ai.google.dev/gemma/docs/core/model_card_3)    | ✅ |
| **meta-llama/Llama-3.3-70B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅|
| **meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅ |
| **meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅ |
| **meta-llama/Meta-Llama-3-8B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅ |
| **meta-llama/Meta-Llama-3-70B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅ |
| **google/gemma-2-27b-it** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅ |
| **google/gemma-2-9b-it** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅  |
| **meta-llama/Meta-Llama-3-70B-Instruct-Turbo** | [together AI](https://docs.together.ai/docs/serverless-models)  | ✅|


## 🚀 How to Run

This script processes tasks defined in YAML configuration files and runs them using a specified model. 
The results are saved in the specified output directory.

### Step 1: Clone the Repository  
Clone the repository to your local machine:
```
git clone https://github.com/McGill-NLP/AfroBench
cd prompt_with_API
```

### Step 2: Install Dependencies and export API Keys 
Install the required Python dependencies:
```
pip install -r requirements.txt 
```
Export API keys, this is optional based on the API in use 
```
export GEMINI_API_KEY=<API KEY>
export OPENAI_API_KEY=<API KEY>
export TOGETHER_API_KEY=<API KEY>
```
### Step 3: Run the script 
``` 
python run.py --tasks <task_file_or_directory> --model <model_name> --output <output_directory>
```
| Argument        | Description                                                                        |
|-----------------|------------------------------------------------------------------------------------|
| `--tasks`       | Path to one or more YAML task files, or a directory containing them.               |
| `--model`       | Name of the model to use for processing as required by the API.                    |
| `--output`      | Directory where results will be saved.                                             |
| `--limit`       | (Optional) Limit the number of samples processed (useful for testing).             |
| `--prompt_no`   | (Optional) Specify a prompt number to run (1-based index).                         |
| `--use_fewshot` | (Optional) Specifies whether or not to run fewshot evaluation for this run `bool`. |


## 🛠️ How to Configure Tasks
This framework supports the tasks evaluated in AfroBench [AfroBench](https://mcgill-nlp.github.io/AfroBench/), but it's designed to be flexible and supports configuring new NLP tasks. Here's how you can configure your own tasks:
### Creating a YAML file

To add a new task, first create a new YAML file that configures the task. We recommend placing your YAML file in the tasks/ directory and naming it according to the dataset or task shorthand. For example:

```sh
touch tasks/<my_new_task_name>.yaml
```
Now, define the task name:
```yaml
name: <task_name>
```

### Selecting and configuring a dataset

This framework uses the HuggingFace [`datasets`](https://github.com/huggingface/datasets) API to manage and download datasets. Before configuring your dataset, check if it is already available on the HuggingFace [Hub](https://huggingface.co/datasets).If not, you can add it to their Hub to make it accessible to a wider user base by following [this guide](https://github.com/huggingface/datasets/blob/main/ADD_NEW_DATASET.md).

Here’s how you can define the dataset and the split you want to use:

```yaml
dataset: <dataset_name>  # the name of the dataset on the HuggingFace Hub
dataset_name: <dataset_configuration>  # optional, if the dataset requires a config
trust_remote_code: <True_or_False>  # whether to trust remote code execution for the dataset
```

Next, specify the test split.:

```yaml
test_split: <split_name>  # specify the test split name (e.g., 'test', 'validation')
```
If your task uses few-shot examples, specify the split and number of examples:
```yaml
num_fewshot: 5  # the number of few-shot examples to use
fewshot_split: <split_name>  # specify the split from which to draw few-shot examples
```
The script is configured to use random n_samples for the fewshot split specified.

List the languages for the dataset to be evaluated in this task (ensure the names match the ones on HuggingFace):
```yaml
languages: 
  - language1
  - language2
```

### Writing the Prompt Templates
This framework supports the use of multiple prompts. Prompts are the format we use to instruct the LM. We need to define the input and output formats.

* `target`: specifies the dataset column name that contains the targets/answers
* `target_prefix` and `target_suffix` a variation that accounts for when target is the language code precluded by a prefix or followed by a suffix as is common in most translation dataset. 
* `choices` similar to the lm-harness `doc_to_choice`. Sets the appropriate list of possible choice strings
* `prompts` input prompt in text with the use of placeholders source sentences and languages if applicable. Placeholders are created with by adding curly brackets to the text. Common placeholders includes; 
  * {{source}} - source language 
  * {{target}} - target language (useful for translation tasks)
  * {{source_column}} - name of dataset column containing source target
Placeholders are relative and can be used to represent any column value in the dataset. See `flores.yaml`, `openai_mmlu.yaml` and `afrisenti.yaml` tasks for examples. 
```yaml
target: <target_column_name>
prompt:
  - prompt1
  - prompt2
  - prompt3
  - prompt4
  - prompt5
choices:
  - option1
  - option2
  - option3
  - option4
```

## 📶 Defining Metrics
To evaluate the model's performance, you need to specify one or more metrics. The currently supported metrics include:
* `acc`
* `f1`
* `exact_match`
* `bert_score`
* `bleu`; uses `sacrebleu`
* `chrf`; uses `sacrebleu`
* `span_f1`; for calculating token classification f1_score 
* `acc_pos`; for calculating accuracy score in port of speech tagging
Add the metrics you wish to use for your task:
```yaml
metrics:
  - acc
  - span_f1
```

## Post Processes
If your tasks require the use of verbalizer to extract the key response or words that's synonymous to the expected 
target, include the verbalizer in the task yaml. See `masakhanews.yaml` for sample
```yaml
verbalizer:
  key1: value
  key2: ["synonym1", "synonym2", "synonym3"]
```
Some tasks might require you to map the model response to target. This is useful when the target has been encoded. 
```yaml
  value1: code1
  value2: code2
```

### Example Task YAML File
```yaml
name: my_new_task
dataset: my_dataset
test_split: test
languages:
  - en
  - es
num_fewshot: 3
fewshot_split: validation
target: answer
prompts:
  - "Question: {{question}}\nChoices: {{choices}}\nAnswer: . Return only one of 'A', 'B', 'C', or 'D'"
choices:
  - A
  - B
  - C
  - D
metrics:
  - accuracy
  - f1
verbalizer:
  "Yes": ["affirmative"]
  "No": ["negative"]
```

## Submitting your task
You're all set! By following the steps above, you can easily add new tasks, configure datasets, and run evaluations. 
If you encounter any issues, feel free to refer to the examples or raise an issue in the repository.
Push your work and make a pull request to the main branch! Thanks for the contribution :).
Happy evaluating! 🚀