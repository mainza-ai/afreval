"""ParallelCorpus protocol and registry."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


class AlignmentError(ValueError):
    pass


@runtime_checkable
class ParallelCorpus(Protocol):
    id: str

    def languages(self) -> list[str]:
        """Return available language codes (ISO 639-3)."""
        ...

    def load(self, languages: list[str], split: str = "devtest") -> dict[str, list[str]]:
        """
        Return aligned sentence lists keyed by ISO 639-3 language code.
        All lists must be the same length; raises AlignmentError otherwise.
        """
        ...


class CorpusRegistry:
    def __init__(self) -> None:
        self._corpora: dict[str, ParallelCorpus] = {}

    def register(self, corpus: ParallelCorpus) -> None:
        self._corpora[corpus.id] = corpus

    def get(self, id: str) -> ParallelCorpus:
        try:
            return self._corpora[id]
        except KeyError:
            raise KeyError(f"Corpus '{id}' not found. Available: {self.list_ids()}")

    def list_ids(self) -> list[str]:
        return sorted(self._corpora.keys())

    def list_all(self) -> list[ParallelCorpus]:
        return [self._corpora[k] for k in self.list_ids()]


CORPUS_REGISTRY = CorpusRegistry()


def _check_alignment(sentences: dict[str, list[str]]) -> None:
    lengths = {lang: len(sents) for lang, sents in sentences.items()}
    if len(set(lengths.values())) > 1:
        detail = ", ".join(f"{l}={n}" for l, n in lengths.items())
        raise AlignmentError(f"Sentence counts are not equal: {detail}")
