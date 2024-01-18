import json
import os
import subprocess
import tempfile
from typing import List

import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt')
from vale import download_vale_if_missing


def process_with_vale(input_text: str) -> List[str]:
    """
    Process the input text using Vale and extract sentences with passive voice matches.

    Args:
        input_text (str): The input text to be processed.

    Returns:
        List[str]: A list of sentences containing passive voice matches.
    """
    
    vale_bin_path = download_vale_if_missing()

    def create_temp_markdown(text):
        """
        Create a temporary markdown file with the given text.

        Args:
            text (str): The text to be written to the temporary file.

        Returns:
            str: The path of the created temporary file.
        """
        temp_dir = tempfile.gettempdir()
        temp_file = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".md", dir=temp_dir)
        temp_file.write(text)
        temp_file.flush()
        temp_file_name = temp_file.name
        temp_file.close()
        return temp_file_name

    tmp_filename = create_temp_markdown(input_text)

    vale_command = [vale_bin_path, "--output=JSON", "--config", "vale.ini", tmp_filename]

    # Run Vale using the subprocess module
    try:
        result = subprocess.run(vale_command, capture_output=True, text=True, check=True)
        output_json = result.stdout
    except subprocess.CalledProcessError as e:
        output_json = ""

    os.remove(tmp_filename)

    output = json.loads(output_json)

    def extract_sentences_with_matches(line_text, entries):
        """
        Extract sentences and their corresponding matches from the line.

        Args:
            line_text (str): The text of the line.
            entries (list): A list of entries containing match information.

        Returns:
            dict: A dictionary where the keys are sentences and the values are dictionaries containing the matches found in each sentence.
        """
        sentences = sent_tokenize(line_text)
        sentence_matches = {}
        for entry in entries:
            match = entry["Match"]
            span_start, span_end = entry["Span"]
            for sentence in sentences:
                if sentence.find(line_text[span_start:span_end]) != -1:
                    if sentence not in sentence_matches:
                        sentence_matches[sentence] = {"matches": []}
                    sentence_matches[sentence]["matches"].append(match)
        return sentence_matches

    # Extract sentences with passive voice matches
    passive_sentences_with_matches = {}
    for file_path in output:
        entries_by_line = {}
        for entry in output[file_path]:
            line_number = entry["Line"]
            if line_number not in entries_by_line:
                entries_by_line[line_number] = []
            entries_by_line[line_number].append(entry)
        
        # Process each line
        for line_number, entries in entries_by_line.items():
            lines = input_text.split('\n')
            if line_number - 1 < len(lines):
                line_text = lines[line_number - 1]
                sentences_with_matches = extract_sentences_with_matches(line_text, entries)
                passive_sentences_with_matches.update(sentences_with_matches)

    list_of_passive_sentences = list(passive_sentences_with_matches.keys())

    return list_of_passive_sentences