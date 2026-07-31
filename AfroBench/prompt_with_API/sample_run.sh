#!/bin/bash

# run all afrobench_lite tasks
python run.py --tasks afrobench_lite --model 'gemini-2.0-flash' --output './results'

# run all afrobench tasks
python run.py --tasks afrobench_tasks --model 'gemini-2.0-flash' --output './results'

# or run specific tasks
python run.py --tasks afrobench_tasks/flores.yaml --model 'gemini-2.0-flash' --output './results'