import json
import logging
import os
import subprocess
import tempfile
from difflib import SequenceMatcher
from typing import Dict, List, Tuple

import nltk
from nltk.tokenize import sent_tokenize
from vale import download_vale_if_missing

nltk.download('punkt')


def process_with_vale(input_text: str) -> Tuple[Dict[str, Dict[str, List[str]]], Dict[str, Dict[str, str]]]:
    """
    Analyzes input text with Vale, returning a tuple containing:
    1) A mapping of sentences to their rule violations.
    2) A dictionary of unique checks with descriptions and links.

    Args:
        input_text (str): Text to be analyzed.

    Returns:
        Tuple[Dict[str, Dict[str, List[str]]], Dict[str, Dict[str, str]]]:
        1) Mapping of sentences to a dictionary with a "violations" key listing rule violations.
        2) Dictionary of unique checks with 'Description' and 'Link'.
    """
    vale_bin_path = download_vale_if_missing()

    def create_temp_markdown(text: str) -> str:
        """
        Creates a temporary markdown file for the given text.

        Args:
            text (str): Text to be written to a file.

        Returns:
            str: Path to the created temporary markdown file.
        """
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md", dir=temp_dir)
        temp_file.write(text)
        temp_file.flush()
        temp_file_name = temp_file.name
        temp_file.close()
        return temp_file_name

    tmp_filename = create_temp_markdown(input_text)

    vale_command = [vale_bin_path, "--output=JSON", tmp_filename]

    # Run Vale using the subprocess module
    try:
        result = subprocess.run(vale_command, capture_output=True, text=True, check=True)
        output_json = result.stdout
        output = json.loads(output_json)
    except subprocess.CalledProcessError as e:
        output = {}

    os.remove(tmp_filename)

    sentences_with_violations = {}
    unique_checks = {}

    # Tokenize the input text into sentences for matching
    sentences = sent_tokenize(input_text)

    for _, issues in output.items():
        for issue in issues:
            check = issue['Check']
            description = issue['Description']
            link = issue.get('Link', '') or ''

            # Create or update the unique check entry
            unique_checks[check] = {'Description': description, 'Link': link}

            for sentence in sentences:
                if sentence.find(issue['Match']) != -1:
                    if sentence not in sentences_with_violations:
                        sentences_with_violations[sentence] = {"violations": []}
                    if description not in sentences_with_violations[sentence]["violations"]:
                        sentences_with_violations[sentence]["violations"].append(description)

    return sentences_with_violations, unique_checks


def append_violation_fixes(violations, sentences_with_violations, unique_checks):
    """
    Appends links to the clear_explanation of each violation based on matched violations.

    Before appending fixes, it checks if original_sentence in each violation exactly matches sentences in sentences_with_violations. If not, it finds the closest match and updates original_sentence accordingly.

    Args:
        violations: A list of violation objects, each representing a violation with attributes 'original_sentence' and 'clear_explanation'.
        sentences_with_violations: A dictionary mapping original sentences to their violations and descriptions.
        unique_checks: A dictionary mapping violation identifiers to their descriptions and links for fixes.

    Returns:
        None. The function modifies the 'clear_explanation' attribute of each violation in place to include the fixes.
    """
    for active in violations:
        llm_original_sentence = active.original_sentence
        if llm_original_sentence not in sentences_with_violations:
            logging.debug(f"Original sentence produced by LLM not directly found, looking for closest match: {llm_original_sentence}")
            closest_match = None
            highest_similarity_score = 0.0

            for sentence in sentences_with_violations:
                similarity_score = SequenceMatcher(None, llm_original_sentence, sentence).ratio()
                if similarity_score > highest_similarity_score:
                    highest_similarity_score = similarity_score
                    closest_match = sentence

            logging.debug(f"Adjusting sentence based on similarity score {highest_similarity_score}: '{llm_original_sentence}' to '{closest_match}'")
            llm_original_sentence = closest_match

        violations_links = []
        if llm_original_sentence in sentences_with_violations:
            sentence_violations = sentences_with_violations[llm_original_sentence]['violations']
            for violation in sentence_violations:
                if matching_check := next(
                    (
                        check
                        for check, details in unique_checks.items()
                        if violation.strip().lower()
                        == details['Description'].strip().lower()
                    ),
                    None,
                ):
                    violation_link = f"[{violation}]({unique_checks[matching_check]['Link']})"
                    violations_links.append(violation_link)

        fixes_text = "Fixes: " + ", ".join(violations_links)
        if violations_links:
            active.clear_explanation += f" {fixes_text}"
