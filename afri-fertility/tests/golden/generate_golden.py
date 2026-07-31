"""Run this script once to generate golden_counts.json for the golden tests.

Usage:
    python tests/golden/generate_golden.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2] / "src"))

from afri_fertility.tokenizers import REGISTRY
from afri_fertility.tokenizers import tiktoken_adapter  # noqa: F401

SENTENCES = {
    "en_hello": "Hello world",
    "en_pangram": "The quick brown fox jumps over the lazy dog",
    "yor_sample": "Àwọn ará Nàìjíríà tó ń gbé ní ìlú Èkó",
    "hau_sample": "Hausa ta ci gaba da zama harshen sadarwa a Najeriya",
    "amh_sample": "አማርኛ ቋንቋ የኢትዮጵያ ብሔራዊ ቋንቋ ነው",
    "swh_sample": "Kiswahili ni lugha ya taifa ya Tanzania na Kenya",
    "fra_sample": "Le français est une langue romane parlée dans le monde entier",
    "eng_baseline": "English is the most widely used language in the world today",
}

TOKENIZERS = ["openai/o200k_base", "openai/cl100k_base"]

golden = {}
for tok_id in TOKENIZERS:
    adapter = REGISTRY.get(tok_id)
    for label, text in SENTENCES.items():
        key = f"{label}__{tok_id}"
        count = adapter.count(text)
        golden[key] = count
        print(f"{key}: {count}")

out = Path(__file__).parent / "golden_counts.json"
out.write_text(json.dumps(golden, indent=2, sort_keys=True))
print(f"\nWrote {out}")
