import logging
import os
import time
from typing import Dict, Optional, Tuple

from langchain import callbacks
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.utils.function_calling import convert_to_openai_function
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langsmith import Client

from schema import SmartEditorResponse


def get_unique_violations(sentences_with_violations):
    """
    Extracts a sorted list of unique violations from the sentences_with_violations structure.

    Args:
        sentences_with_violations (Dict): A dictionary where keys are sentences and values are dictionaries with a "violations" key listing rule violations for that sentence.

    Returns:
        List[str]: A sorted list of unique violations, each prefixed with "- " for readability.
    """
    unique_violations = set()

    for sentence_info in sentences_with_violations.values():
        for violation in sentence_info["violations"]:
            unique_violations.add(violation)

    return [f"- {violation}" for violation in sorted(unique_violations)]


def determine_llm() -> ChatOpenAI:
    """Determine which LLM to use based on environment variable."""
    model_env = os.getenv("SMARTEDITOR_MODEL")
    if model_env == "openai":
        return ChatOpenAI(verbose=True,
                          temperature=0,
                          model="gpt-4-turbo-preview",
                          max_tokens=4096)
    elif model_env == "openai_azure":
        return AzureChatOpenAI(verbose=True,
                               temperature=0, openai_api_version="2024-02-15-preview",
                               azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                               model="gpt-35-turbo")
    else:
        raise ValueError(f"Unsupported model specified: {model_env}")


def smarteditor(article_text: str, sentences_with_violations: Dict) -> Tuple[SmartEditorResponse, Optional[str]]:
    """
    Processes article text to rewrite sentences based on their style guide violations.

    Args:
        article_text (str): The complete article text to be processed.
        sentences_with_violations (Dict): A dictionary mapping sentences to their respective style guide violations.

    Returns:
        Tuple[SmartEditorResponse, Optional[str]]: A tuple where the first element is an object containing the original and revised sentences along with explanations, and the second element is an optional tracing URL for detailed analysis.
    """
    llm = determine_llm()

    messages = ChatPromptTemplate.from_messages(
        [
            ("system", 
                "You are a world-class expert in revising sentences. For each sentence in the user provided article that violates one or more rules in the custom style guide, use the original sentence and relevent context from the rest of the article to give the following information in JSON format:\n-The original sentence from the article that violates one or more rules of the custom style guide.\n- The revised sentence with no violations.\n- A clear explanation of the revision. \n\nThe user will provide a dictionary containing all the sentences from the article that violate one one or more rules from the custom style guide. Revise all those sentences and only those sentences. Each sentence should be revised to remediate all the rules the user specifies it violates and only those rules."),
            ("human", 
                "Article:\n\n {user_input}\n\n Dictionary containing all sentences from the article that violate one one or more rules from the custom style guide: {sentences_with_violations}."),
        ]
    )

    openai_functions = [convert_to_openai_function(SmartEditorResponse)]
    parser = JsonOutputFunctionsParser()
    chain = messages | llm.bind(functions=openai_functions) | parser

    fixed_sentences = None
    run_url = None

    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    if tracing_enabled:
        client = Client()
        with callbacks.collect_runs() as cb:
            try:
                fixed_sentences = chain.invoke({"user_input": article_text, "custom_style_guide": get_unique_violations(sentences_with_violations), "sentences_with_violations": sentences_with_violations})

                # Ensure that all tracers complete their execution
                wait_for_all_tracers()

                if fixed_sentences:
                    # Get public URL for run
                    run_id = cb.traced_runs[0].id
                    time.sleep(2)
                    client.share_run(run_id)
                    run_url = client.read_run_shared_link(run_id)
            except Exception as e:
                logging.error(f"Error during LLM invocation with tracing: {str(e)}")
    else:
        try:
                fixed_sentences = chain.invoke({"user_input": article_text, "custom_style_guide": get_unique_violations(sentences_with_violations), "sentences_with_violations": sentences_with_violations})
        except Exception as e:
            logging.error(f"Error during LLM invocation without tracing: {str(e)}")

    return SmartEditorResponse.parse_obj(fixed_sentences), run_url