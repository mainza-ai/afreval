from .base import ParallelCorpus, CorpusRegistry, CORPUS_REGISTRY, AlignmentError
from . import flores   # noqa: F401 — registers flores corpus
from . import sib200   # noqa: F401 — registers sib200 corpus
from . import mafand   # noqa: F401 — registers mafand corpus
from .custom import CustomCorpus

__all__ = [
    "ParallelCorpus",
    "CorpusRegistry",
    "CORPUS_REGISTRY",
    "AlignmentError",
    "CustomCorpus",
]
