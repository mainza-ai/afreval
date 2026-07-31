import re
import torch
import sacrebleu
import collections
from typing import List, Tuple
from sklearn.metrics import f1_score, accuracy_score
import evaluate as hf_evaluate


def acc_all(items: List[Tuple[List[str], List[str]]]) -> float:
    """Compute F1 score for binary or multiclass classification."""
    golds, preds = zip(*items)
    return accuracy_score(golds, preds)


def f1_score_metric(items: List[Tuple[str, str]]) -> float:
    """Compute F1 score for binary or multiclass classification."""
    golds, preds = zip(*items)
    return f1_score(golds, preds, average="macro")


def bleu(items: List[Tuple[str, str]]) -> float:
    """Compute BLEU score."""
    refs, preds = zip(*items)
    refs, preds = _sacreformat(refs, preds)
    return sacrebleu.corpus_bleu(preds, refs).score


def chrf(items: List[Tuple[str, str]]) -> float:
    """Compute chrF++ score."""
    refs, preds = zip(*items)
    refs, preds = _sacreformat(refs, preds)
    return sacrebleu.corpus_chrf(preds, refs).score


def bertscore_fn(items: List[Tuple[str, str]])-> float:
    """
  Calculate BERTScore for a set of candidate summaries against reference summaries.
  """
    bertscore = hf_evaluate.load("bertscore")
    model_name = "microsoft/mdeberta-v3-base"
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    references, predictions = zip(*items)
    return bertscore.compute(predictions=predictions, references=references, model_type=model_name, device=device)['f1'][0]


def exact_match_fn(items: List[Tuple[str, str]]) -> float:
    """Compute exact match score."""
    exact_match = hf_evaluate.load("exact_match")
    references, predictions = zip(*items)
    predictions = [str(p).strip() for p in predictions]
    references = [str(r).strip() for r in references]
    return exact_match.compute(predictions=predictions, references=references)["exact_match"]


def _sacreformat(refs, preds):
    """Format inputs for SacreBLEU/chrF++."""
    if isinstance(refs[0], str):
        refs = [[r] for r in refs]
    else:
        refs = list(zip(*refs))
    if isinstance(preds[0], list):
        preds = [" ".join(p) for p in preds]
    return refs, preds


def acc_score_pos(items: List[Tuple[List[int], List[List[int]]]]) -> float:
    """Receives one gold-pred pair"""

    golds, preds = zip(*items)

    def map_pos_tags(value, mapping):
        reversed_mapping = {v.lower(): k for k, v in mapping.items()}
        return [reversed_mapping.get(v, v) for v in value]

    pos_tag_map = {
        0: "NOUN",
        1: "PUNCT",
        2: "ADP",
        3: "NUM",
        4: "SYM",
        5: "SCONJ",
        6: "ADJ",
        7: "PART",
        8: "DET",
        9: "CCONJ",
        10: "PROPN",
        11: "PRON",
        12: "X",
        13: "_",
        14: "ADV",
        15: "INTJ",
        16: "VERB",
        17: "AUX"
    }
    mapped_preds = [map_pos_tags(value, pos_tag_map) for value in preds]

    # Calculate the accuracy for each gold-pred pair
    gold = golds[0]
    pred = mapped_preds[0]
    min_length = min(len(gold), len(pred))
    gold = gold[:min_length]
    pred = pred[:min_length]

    # Calculate accuracy for the current pair and add to the list
    accuracy = accuracy_score(gold, pred)
    return accuracy


def span_f1_seqio(items: List[Tuple[str, str]]):
    """Computes Span based F1 score.

    This function is copied from
    https://github.com/google-research/multilingual-t5/blob/master/multilingual_t5/evaluation/metrics.py

    Returns:
    span f1 across all targets and predictions (Based on CoNLL script)
    """
    unzipped_list = list(zip(*items))
    targets = unzipped_list[0]
    predictions = unzipped_list[1]

    true_positives = collections.defaultdict(int)
    false_positives = collections.defaultdict(int)
    false_negatives = collections.defaultdict(int)

    def normalize_text(strings):
        def get_blank_spaces_pattern():
            return re.compile(r'\s{3,}|\t')

        def remove_blank_spaces(text):
            text = re.sub(pattern=get_blank_spaces_pattern(), repl='', string=text)
            text = re.sub('\s+', ' ', text)
            return text

        def remove_punctuation(text):
            my_punctuation = '!"$%&\'()*+,-./:;<=>?[\\]^_`{|}~•@.""-,`'
            text = re.sub('[' + my_punctuation + ']+', ' ', str(text))  # strip punctuation
            return text

        def remove_articles(text):
            regex = re.compile(r"\b(a|an|the)\b", re.UNICODE)
            return re.sub(regex, " ", text)

        def lowercase(text):
            text = text.lower()
            return text

        strings = remove_punctuation(strings)
        strings = remove_articles(strings)
        strings = remove_blank_spaces(strings)
        strings = lowercase(strings)

        return strings

    def tags_to_spans(tag_sequence, delimiter="$$"):
        """Extract spans from IOB1 or BIO tags."""
        if isinstance(tag_sequence, list):
            tag_sequence = " ".join(i.strip() for i in tag_sequence)
        tag_sequence_split = [item.strip() for sub in tag_sequence.strip().split(delimiter) for item in sub.split('$') if item]
        tag_sequence_split = [item.strip() for value in tag_sequence_split for sub in value.split(". ") for item in sub.split(", ")]
        tags_entities = []
        for tag_entity in tag_sequence_split:
            tag_entity_split = tag_entity.split(": ")
            if len(tag_entity_split) != 2:
                continue
            tag = normalize_text(tag_entity_split[0].strip())
            entity = normalize_text(tag_entity_split[1].rstrip().lstrip())
            tags_entities.append((tag, entity))
        return tags_entities

    def compute_f1_metrics(true_positive, false_positive, false_negative):
        precision = float(true_positive) / float(
            true_positive + false_positive + 1e-13
        )
        recall = float(true_positive) / float(
            true_positive + false_negative + 1e-13
        )
        f1_measures = 2.0 * ((precision * recall) / (precision + recall + 1e-13))
        return precision, recall, f1_measures

    for target, pred in zip(targets, predictions):
        gold_spans = tags_to_spans(target)
        predicted_spans = tags_to_spans(pred)

        for span in predicted_spans:
            if span in gold_spans:
                true_positives[span[0]] += 1
                gold_spans.remove(span)
            else:
                false_positives[span[0]] += 1

        # These spans weren't predicted.
        for span in gold_spans:
            false_negatives[span[0]] += 1

    _, _, f1_measure = compute_f1_metrics(
        sum(true_positives.values()),
        sum(false_positives.values()),
        sum(false_negatives.values()),
    )
    return f1_measure
