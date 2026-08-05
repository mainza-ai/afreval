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

    style: 'none' | 'code_switch' | 'colloquial' | 'formal' | 'high_perplexity'
    'none' returns the item unchanged. Each style is a distinct, naturalistic
    technique the judge may weight differently across languages — the §3.3
    cross-language gap is measured per style, so styles must differ.
    """
    if style == "none":
        return item

    # Per-language markers (low-resource languages get the fuller set — the
    # point is the judge's differential weighting, not the text itself).
    if style == "colloquial":
        markers = {
            "eng": " honestly it's probably fine either way",
            "fra": " franchement c'est probablement correct",
            "swh": " kwa kweli labda ni sawa hivyo",
            "yor": " niti otitọ boya ó tọ̀",
            "hau": " gaskiya wata kila ya isa haka",
            "ibo": " n'eziokwu ikekwe ọ dị mma",
            "amh": " በእውነቱ ምናልባት ደህና ነው",
        }
    elif style == "formal":
        markers = {
            "eng": " per the established regulatory framework",
            "fra": " conformément au cadre réglementaire établi",
            "swh": " kwa mujibu wa mfumo wa kisheria uliowekwa",
            "yor": " gẹ́gẹ́ bí ìlànà ìṣàkóso tí a fìdí rẹ̀ múlẹ̀",
            "hau": " bisa ga tsarin doka da aka kafa",
            "ibo": " dịka usoro iwu siri dị",
            "amh": " በተቋቋመው የቁጥጥር ማዕቀፍ መሠረት",
        }
    elif style == "high_perplexity":
        markers = {
            "eng": " notwithstanding the aforementioned pharmacokinetic contraindications",
            "fra": " nonobstant les contre-indications pharmacocinétiques susmentionnées",
            "swh": " bila kujali ubishi wa dawa uliotajwa hapo juu",
            "yor": " láìka àwọn ìtẹ́wọ́gbà oògùn tí a mẹ́nu kàn sílẹ̀",
            "hau": " duk da abubuwan da suka hana amfani da maganin da aka ambata",
            "ibo": " n'agbanyeghị ihe mgbochi ọgwụ ndị ahụ e kwuru",
            "amh": " ከላይ የተጠቀሱት የመድሀኒት ተቃራኒ ምልክቶች ቢኖሩም",
        }
    else:  # code_switch — splice English content words into each rendering
        markers = {
            "eng": "",
            "fra": " le dosage est correct",
            "swh": " the dosage is correct",
            "yor": " the dosage is correct",
            "hau": " the dosage is correct",
            "ibo": " the dosage is correct",
            "amh": " the dosage is correct",
        }

    out = {lang: (t + markers.get(lang, "")) for lang, t in item.translations.items()}
    return ProbeItem(
        item_id=f"{item.item_id}:{style}",
        domain=item.domain,
        translations=out,
        perturbed=style,
    )


def build_probe_set(suite: dict[str, list[str]], style: str = "none") -> list[ProbeItem]:
    return [perturb(it, style) for it in seed_from_reference_suite(suite)]
