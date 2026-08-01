"""§3.3 perturbation-generation strategy — THE MUTABLE ARTIFACT.

The probe agent edits THIS file to add perturbation techniques. The judge
harness (judge/) and run_probe.py are frozen. Output: list of ProbeItem,
each with semantically identical per-language renderings that the judge will
score for the cross-language acceptance gap.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProbeItem:
    item_id: str
    domain: str
    translations: dict[str, str]
    perturbed: str = ""  # perturbation applied (for provenance)


def seed_from_reference_suite(suite: dict[str, list[str]]) -> list[ProbeItem]:
    """Semantically identical content from the pinned reference suite."""
    items: list[ProbeItem] = []
    languages = list(suite.keys())
    n = min(len(v) for v in suite.values())
    for i in range(n):
        items.append(
            ProbeItem(
                item_id=f"ref-{i:03d}",
                domain="health",
                translations={lang: suite[lang][i] for lang in languages},
            )
        )
    return items


def perturb(item: ProbeItem, style: str) -> ProbeItem:
    """Apply a perturbation to the per-language renderings.

    style: 'none' | 'code_switch' | 'formal' | 'colloquial' | 'high_perplexity'
    The agent implements these. 'none' returns the item unchanged.
    """
    if style == "none":
        return item
    # Placeholder strategy: append a naturalistic filler the judge may weight
    # differently across languages (e.g. uncertainty hedging in low-resource
    # renderings). The agent replaces this with real techniques.
    fillers = {
        "eng": "",
        "fra": "",
        "swh": " labda",
        "yor": " boya",
        "hau": " wata kila",
        "ibo": " ikekwe",
        "amh": " ምናልባት",
    }
    out = {lang: (t + fillers.get(lang, "")) for lang, t in item.translations.items()}
    return ProbeItem(
        item_id=f"{item.item_id}:{style}",
        domain=item.domain,
        translations=out,
        perturbed=style,
    )


def build_probe_set(suite: dict[str, list[str]], style: str = "none") -> list[ProbeItem]:
    return [perturb(it, style) for it in seed_from_reference_suite(suite)]
