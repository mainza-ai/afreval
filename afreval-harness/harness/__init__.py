"""afreval-harness — frozen evaluation substrate for Milimo AfrEval.

Phase 0 artifact. Nothing downstream (tokenizer research, Context Score,
edge ASR, BiasScope) starts until the pins in pins/ and the checksums in
checksums/ are frozen and tagged. This package is READ-ONLY by agents: the
code here is ground truth, versioned and pinned like a test suite.
"""

from .pins import load_pin, PIN_DIR
from .tokenizer_eval import TokenizerEval, script_stratify, english_cpt_regression
from .waxal_eval import wer, cer, score_transcription

__all__ = [
    "load_pin",
    "PIN_DIR",
    "TokenizerEval",
    "script_stratify",
    "english_cpt_regression",
    "wer",
    "cer",
    "score_transcription",
]

__version__ = "0.1.0"
