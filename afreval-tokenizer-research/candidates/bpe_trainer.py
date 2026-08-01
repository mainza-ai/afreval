"""Compact BPE trainer + candidate for the §3.1 search loop.

Standard byte-pair encoding over character units (script-agnostic — Ethiopic,
N'Ko, Latin all count per code point). The candidate implements the harness
protocol (.id, .count) and applies merges by rank (lowest first, all
occurrences per pass — matching training).
"""
from __future__ import annotations

import re
from collections import Counter

WORD_SPLIT = re.compile(r"\s+")


def train_bpe(words: list[str], num_merges: int) -> list[tuple[str, str]]:
    units: list[list[str]] = [list(w) for w in words]
    merges: list[tuple[str, str]] = []
    for _ in range(num_merges):
        counts: Counter = Counter()
        for u in units:
            for i in range(len(u) - 1):
                counts[(u[i], u[i + 1])] += 1
        if not counts:
            break
        (a, b), _ = counts.most_common(1)[0]
        merges.append((a, b))
        new_units = []
        for u in units:
            merged: list[str] = []
            i = 0
            while i < len(u):
                if i + 1 < len(u) and u[i] == a and u[i + 1] == b:
                    merged.append(a + b)
                    i += 2
                else:
                    merged.append(u[i])
                    i += 1
            new_units.append(merged)
        units = new_units
    return merges


class BPECandidate:
    def __init__(self, merges: list[tuple[str, str]], tokenizer_id: str):
        self.id = tokenizer_id
        self._rank = {pair: i for i, pair in enumerate(merges)}

    def _merge_word(self, word: str) -> list[str]:
        units = list(word)
        while True:
            best_pair = None
            best_rank = None
            for i in range(len(units) - 1):
                r = self._rank.get((units[i], units[i + 1]))
                if r is not None and (best_rank is None or r < best_rank):
                    best_rank = r
                    best_pair = (units[i], units[i + 1])
            if best_pair is None:
                break
            new: list[str] = []
            i = 0
            while i < len(units):
                if i + 1 < len(units) and (units[i], units[i + 1]) == best_pair:
                    new.append(units[i] + units[i + 1])
                    i += 2
                else:
                    new.append(units[i])
                    i += 1
            units = new
        return units

    def count(self, text: str) -> int:
        total = 0
        for w in WORD_SPLIT.split(text):
            if w:
                total += len(self._merge_word(w))
        return total
