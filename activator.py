import logging
import os
import time
from typing import Optional, Tuple

from langchain import callbacks
from langchain.callbacks.tracers.langchain import wait_for_all_tracers
from langchain.chains.openai_functions import create_structured_output_runnable
from langchain.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langsmith import Client

from schema import ActivatorResponse


def determine_llm() -> ChatOpenAI:
    """Determine which LLM to use based on environment variable."""
    model_env = os.getenv("ACTIVATOR_MODEL")
    if model_env == 'openai':
        return ChatOpenAI(verbose=True, 
                          temperature=0, 
                          model="gpt-4-turbo-preview", 
                          max_tokens=4096)
    elif model_env == 'openai_azure':
        return AzureChatOpenAI(verbose=True, 
                               temperature=0, openai_api_version="2024-02-15-preview",
                               azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
                               model="1106-Preview", 
                               max_tokens=4096)
    else:
        raise ValueError(f"Unsupported model specified: {model_env}")

def activator(input_text: str, passive_sentences: list) -> Tuple[ActivatorResponse, Optional[str]]:

    """
    Processes input text to rewrite sentences from passive to active voice.

    Args:
        input_text (str): The complete article text.
        passive_sentences (list): A list of sentences identified as being in passive voice.

    Returns:
        ActivatorResponse: An object containing the original sentences, their active voice counterparts, and explanations for the transformations. Also includes an optional tracing URL.
    """
    llm = determine_llm()


    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
"""You are a world-class expert in rewriting sentences from the passive voice to the active voice. For each instance of a sentence written in passive voice in the user-provided article, use the original sentence and context from the rest of the article to provide the following information in JSON format:

- The original sentence from the article containing instance(s) of passive voice.
- The revised sentence in active voice.
- A clear explanation of the choice of subject.

For each sentence, the subject of the active voice should be as precise as possible, considering the relevant context from the full article. If the subject is ambiguous, include a note in the explanation."""
            ),
            (
                "human",
"""Article:

{input}
"""
            ),
            (
                "human",
f"Tip: list of all the sentences written in passive voice in the article: {str(passive_sentences)}"
            ),
        ]
    )

    runnable = create_structured_output_runnable(ActivatorResponse, llm, prompt)

    active_sentences = None
    run_url = None

    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "").lower() == "true"
    if tracing_enabled:
        client = Client()
        with callbacks.collect_runs() as cb:
            try:
                active_sentences = runnable.invoke({"input": input_text})
                # Ensure that all tracers complete their execution
                wait_for_all_tracers()

                if active_sentences:
                    # Get public URL for run
                    run_id = cb.traced_runs[0].id
                    time.sleep(2)
                    client.share_run(run_id)
                    run_url = client.read_run_shared_link(run_id)
            except Exception as e:
                logging.error(f"Error during LLM invocation with tracing: {str(e)}")
    else:
        try:
            active_sentences = runnable.invoke({"input": input_text})
        except Exception as e:
            logging.error(f"Error during LLM invocation without tracing: {str(e)}")

    return active_sentences, run_url
