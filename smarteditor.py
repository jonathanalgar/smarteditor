import logging
import os
import time
from typing import Dict, List, Optional, Tuple

from langchain import callbacks
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage

from schema import SmartEditorResponse


def get_unique_violations(sentences_with_violations):
    """
    Extract a list of unique violations from the given structure.
    """
    unique_violations = set()
    
    for sentence_info in sentences_with_violations.values():
        for violation in sentence_info["violations"]:
            unique_violations.add(violation)
    
    formatted_violations = [f"- {violation}" for violation in sorted(unique_violations)]
    
    return formatted_violations

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
                               model="1106-Preview", 
                               max_tokens=4096)
    else:
        raise ValueError(f"Unsupported model specified: {model_env}")

def smarteditor(input_text: str, sentences_with_violations: Dict) -> Tuple[SmartEditorResponse, Optional[str]]:
    """
    Processes input text to rewrite sentences based on their style guide violations.

    Args:
        input_text (str): The complete article text.
        passive_sentences (list): A list of sentences identified as being in passive voice.

    Returns:
        SmartEditorResponse: An object containing the original sentences, their revised counterparts, and explanations for the transformations. Also includes an optional tracing URL.
    """
    llm = determine_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=f"You are a world-class expert in rewriting sentences based on the requirements of a custom style guide. For each instance of a sentence in the user provided article that violates one or more rules in the custom style guide, use the original sentence and any relevent context from the rest of the article to give the following information in JSON format:\n-The original sentence from the article that violates one or more rules of the custom style guide.\n- The revised sentence with no violations.\n- A clear explanation of the revision.\n\n Custom style guide: {str(get_unique_violations(sentences_with_violations))}"
            ),
            HumanMessage(
                content="Article: {input}"
            ),
            HumanMessage(
                content=f"Tip: dictionary containing all sentences from the article that violate one one or more rules from the custom style guide. The value for each sentence key is a dictionary with a violations key which contains the list of all the rules the sentence violated: {str(sentences_with_violations)}"
            ),
        ]
    )

    runnable = create_structured_output_runnable(SmartEditorResponse, llm, prompt)

    fixed_sentences = None
    run_url = None

    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    if tracing_enabled:
        client = Client()
        with callbacks.collect_runs() as cb:
            try:
                fixed_sentences = runnable.invoke({"input": input_text})
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
            fixed_sentences = runnable.invoke({"input": input_text})
        except Exception as e:
            logging.error(f"Error during LLM invocation without tracing: {str(e)}")

    return fixed_sentences, run_url
