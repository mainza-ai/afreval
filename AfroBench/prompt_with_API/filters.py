import re
import string
from typing import List


def decontaminate_response(prompts: List[str], responses: List[str]) -> List[str]:
    """
    Removes any prompt text that is repeated in the corresponding response.
    Args:
        prompts: List of prompt strings.
        responses: List of response strings.

    Returns:
        List of decontaminated responses.
    """
    return [
        re.sub(re.escape(prompt), "", response, flags=re.IGNORECASE).strip().lstrip()
        for prompt, response in zip(prompts, responses)
    ]


def decontaminate_mt_response(prompts: List[str], responses: List[str]) -> List[str]:
    """
    Extracts the translated sentence from model responses by removing prompt text
    and handling common patterns.

    Args:
        prompts: List of prompt strings.
        responses: List of response strings.

    Returns:
        List of cleaned responses with only the translated sentence.
    """
    decontaminated = []
    for prompt, response in zip(prompts, responses):
        # Remove prompt tex
        response_cleaned = re.sub(re.escape(prompt), "", response, flags=re.IGNORECASE).strip()

        # Extract quoted text that is likely the translation
        match = re.search(r'"([^"]+)"', response_cleaned)
        if match:
            # Take the first quoted segment as the translation
            decontaminated.append(match.group(1))
        else:
            response_cleaned = re.sub(
                r"(can be translated to|translates to|translates|is translated|means| [^ ]+).*?:?",
                "",
                response_cleaned,
                flags=re.IGNORECASE,
            ).strip()
            # Further remove any leading/trailing phrases or colons
            response_cleaned = re.sub(r"^(the |this )?(sentence|phrase|word|text) .*?[:\-]?", "", response_cleaned,
                                      flags=re.IGNORECASE).strip()
            decontaminated.append(response_cleaned)

    return decontaminated


def filter_response(
        responses: List[str], choices: List[str], verbalizer: dict = None
) -> List[str]:
    """
    Filters the model responses using choices and verbalizer in batch.
    Args:
        responses: List of raw model responses.
        choices: List of valid choices.
        verbalizer: Dictionary mapping verbalized phrases to standardized choices.

    Returns:
        List of filtered responses.
    """
    # Pre-compile regex patterns for choices
    choice_patterns = {choice: re.compile(rf"\b{re.escape(choice)}\b", re.IGNORECASE) for choice in choices}

    filtered = []
    for response in responses:
        matched = None
        # Check against choices
        for choice, pattern in choice_patterns.items():
            if pattern.search(response):
                matched = choice

                break

        # Check against verbalizer if no match found
        if not matched and verbalizer:
            for key, synonyms in verbalizer.items():
                for synonym in synonyms:
                    # Use \b for word boundaries to avoid matching parts of words
                    if re.search(rf"\b{re.escape(synonym)}\b", response.lower(), re.IGNORECASE):
                        matched = key
                        break
                if matched:
                    break
        # Append result
        filtered.append(matched if matched else "invalid")

    return filtered


def format_span(responses: List[str]):
    def format_ner_text(text):
        label_dict = {'person': 'PER',
                      'location': 'LOC',
                      'organization': 'ORG',
                      'counties': 'LOC',
                      'places': 'LOC',
                      'people': 'PER',
                      'persons': 'PER',
                      'company': 'ORG',
                      'country': 'LOC',
                      'continent': 'LOC',
                      'time': 'DATE',
                      'date': 'DATE',
                      'per': 'PER',
                      'loc': 'LOC',
                      'org': 'ORG'}
        text = text.lower()
        for key, value in label_dict.items():
            text = text.replace(key, value)

        text = "$".join(i for i in text.split('$$'))
        return text.rstrip('$$')

    def format_named_entities(text):
        """
        Extract named entities from text and format them as 'label: value $$ label: value'.
        Handles grouped entities (e.g., LOC: kenya, uganda) and excludes 'none' values.
        """
        # Regular expression to match label: entities pattern
        pattern = r"\b(PER|LOC|ORG|DATE):\s*([^$]+)"
        # Normalize newline characters
        text = text.replace("\n", "$").strip()
        matches = re.findall(pattern, text)

        formatted_entities = []

        for label, values in matches:
            # Split multiple entities separated by commas and strip whitespace
            entities = [value.strip() for value in values.split(",")]

            # Exclude 'none' entities
            for entity in entities:
                if entity.lower() != "none":
                    formatted_entities.append(f"{label.lower()}: {entity}")

        # Join entities with the desired separator
        return " $ ".join(formatted_entities)

    return [format_named_entities(format_ner_text(resp.lower())) for resp in responses]


def extract_pos(responses: List[str], fallback: List[str] = None):
    if fallback is None:
        fallback = ['invalid']

    def extract_tagged_tokens(text):
        # Extract tagged tokens list from text input using regex
        tokens = re.findall(r"\('([^']*)', '([^']*)'\)", text)
        return [(token, pos) for token, pos in tokens]

    def extract_pos_tags(result):
        pos_tags = []
        if isinstance(result, str):
            result = extract_tagged_tokens(result)
        pos_tags.extend(pos for _, pos in result)
        return pos_tags if pos_tags else fallback

    return [extract_pos_tags(resp) for resp in responses]


def extract_regex(responses: List[str], pattern=r'(-?[$0-9.,]{2,})|(-?[0-9]+)'):
    regex = re.compile(pattern)

    def match_regex(text):
        match = regex.findall(str(text))
        if match:
            match = match[-1]
            if isinstance(match, tuple):
                match = [m for m in match if m][0]
            match = match.strip()
            return match.translate(str.maketrans('', '', string.punctuation))
        return "invalid"

    return [match_regex(resp.strip()) for resp in responses]
