import logging
from typing import List, Optional

from fastapi import HTTPException
from pydantic import BaseModel, Field

SmartEditorRequest_text_example = """# How to work with large language models\n\n## How large language models work\n\n[Large language models][Large language models Blog Post] are functions that map text to text. Given an input string of text, a large language model predicts the text that should come next.\n\nThe magic of large language models is that by being trained to minimize this prediction error over vast quantities of text, the models end up learning concepts useful for these predictions. For example, they learn:\n\n* how to spell\n* how grammar works\n* how to paraphrase\n* how to answer questions\n* how to hold a conversation\n* how to write in many languages\n* how to code\n* etc.\n\nThey do this by \u201creading\u201d a large amount of existing text and learning how words tend to appear in context with other words, and uses what it has learned to predict the next most likely word that might appear in response to a user request, and each subsequent word after that.\n\nGPT-3 and GPT-4 power [many software products][OpenAI Customer Stories], including productivity apps, education apps, games, and more.\n\n## How to control a large language model\n\nOf all the inputs to a large language model, by far the most influential is the text prompt.\n\nLarge language models can be prompted to produce output in a few ways:\n\n* **Instruction**: Tell the model what you want\n* **Completion**: Induce the model to complete the beginning of what you want\n* **Scenario**: Give the model a situation to play out\n* **Demonstration**: Show the model what you want, with either:\n  * A few examples in the prompt\n  * Many hundreds or thousands of examples in a fine-tuning training dataset\n\nAn example of each is shown below.\n\n### Instruction prompts\n\nWrite your instruction at the top of the prompt (or at the bottom, or both), and the model will do its best to follow the instruction and then stop. Instructions can be detailed, so don't be afraid to write a paragraph explicitly detailing the output you want, just stay aware of how many [tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them) the model can process.\n\nExample instruction prompt:\n\n```text\nExtract the name of the author from the quotation below.\n\n\u201cSome humans theorize that intelligent species go extinct before they can expand into outer space. If they're correct, then the hush of the night sky is the silence of the graveyard.\u201d\n\u2015 Ted Chiang, Exhalation\n```\n\nOutput:\n\n```text\nTed Chiang\n```\n\n### Completion prompt example\n\nCompletion-style prompts take advantage of how large language models try to write text they think is mostly likely to come next. To steer the model, try beginning a pattern or sentence that will be completed by the output you want to see. Relative to direct instructions, this mode of steering large language models can take more care and experimentation. In addition, the models won't necessarily know where to stop, so you will often need stop sequences or post-processing to cut off text generated beyond the desired output.\n\nExample completion prompt:\n\n```text\n\u201cSome humans theorize that intelligent species go extinct before they can expand into outer space. If they're correct, then the hush of the night sky is the silence of the graveyard.\u201d\n\u2015 Ted Chiang, Exhalation\n\nThe author of this quote is\n```\n\nOutput:\n\n```text\n Ted Chiang\n```\n\n### Scenario prompt example\n\nGiving the model a scenario to follow or role to play out can be helpful for complex queries or when seeking imaginative responses. When using a hypothetical prompt, you set up a situation, problem, or story, and then ask the model to respond as if it were a character in that scenario or an expert on the topic.\n\nExample scenario prompt:\n```text\nYour role is to extract the name of the author from any given text\n\n\u201cSome humans theorize that intelligent species go extinct before they can expand into outer space. If they're correct, then the hush of the night sky is the silence of the graveyard.\u201d\n\u2015 Ted Chiang, Exhalation\n```\n\nOutput:\n\n```text\n Ted Chiang\n```\n\n### Demonstration prompt example (few-shot learning)\n\nSimilar to completion-style prompts, demonstrations can show the model what you want it to do. This approach is sometimes called few-shot learning, as the model learns from a few examples provided in the prompt.\n\nExample demonstration prompt:\n\n```text\nQuote:\n\u201cWhen the reasoning mind is forced to confront the impossible again and again, it has no choice but to adapt.\u201d\n\u2015 N.K. Jemisin, The Fifth Season\nAuthor: N.K. Jemisin\n\nQuote:\n\u201cSome humans theorize that intelligent species go extinct before they can expand into outer space. If they're correct, then the hush of the night sky is the silence of the graveyard.\u201d\n\u2015 Ted Chiang, Exhalation\nAuthor:\n```\n\nOutput:\n\n```text\n Ted Chiang\n```\n\n### Fine-tuned prompt example\n\nWith enough training examples, you can [fine-tune][Fine Tuning Docs] a custom model. In this case, instructions become unnecessary, as the model can learn the task from the training data provided. However, it can be helpful to include separator sequences (e.g., `->` or `###` or any string that doesn't commonly appear in your inputs) to tell the model when the prompt has ended and the output should begin. Without separator sequences, there is a risk that the model continues elaborating on the input text rather than starting on the answer you want to see.\n\nExample fine-tuned prompt (for a model that has been custom trained on similar prompt-completion pairs):\n\n```text\n\u201cSome humans theorize that intelligent species go extinct before they can expand into outer space. If they're correct, then the hush of the night sky is the silence of the graveyard.\u201d\n\u2015 Ted Chiang, Exhalation\n\n###\n\n\n```\n\nOutput:\n\n```text\n Ted Chiang\n```\n\n## Code Capabilities\n\nLarge language models aren't only great at text - they can be great at code too. OpenAI's [GPT-4][GPT-4 and GPT-4 Turbo] model is a prime example.\n\nGPT-4 powers [numerous innovative products][OpenAI Customer Stories], including:\n\n* [GitHub Copilot] (autocompletes code in Visual Studio and other IDEs)\n* [Replit](https://replit.com/) (can complete, explain, edit and generate code)\n* [Cursor](https://cursor.sh/) (build software faster in an editor designed for pair-programming with AI)\n\nGPT-4 is more advanced than previous models like `text-davinci-002`. But, to get the best out of GPT-4 for coding tasks, it's still important to give clear and specific instructions. As a result, designing good prompts can take more care.\n\n### More prompt advice\n\nFor more prompt examples, visit [OpenAI Examples][OpenAI Examples].\n\nIn general, the input prompt is the best lever for improving model outputs. You can try tricks like:\n\n* **Be more specific** E.g., if you want the output to be a comma separated list, ask it to return a comma separated list. If you want it to say \"I don't know\" when it doesn't know the answer, tell it 'Say \"I don't know\" if you do not know the answer.' The more specific your instructions, the better the model can respond.\n* **Provide Context**: Help the model understand the bigger picture of your request. This could be background information, examples/demonstrations of what you want or explaining the purpose of your task.\n* **Ask the model to answer as if it was an expert.** Explicitly asking the model to produce high quality output or output as if it was written by an expert can induce the model to give higher quality answers that it thinks an expert would write. Phrases like \"Explain in detail\" or \"Describe step-by-step\" can be effective.\n* **Prompt the model to write down the series of steps explaining its reasoning.** If understanding the 'why' behind an answer is important, prompt the model to include its reasoning. This can be done by simply adding a line like \"[Let's think step by step](https://arxiv.org/abs/2205.11916)\" before each answer.\n\n\n\n[Fine Tuning Docs]: https://platform.openai.com/docs/guides/fine-tuning\n[OpenAI Customer Stories]: https://openai.com/customer-stories\n[Large language models Blog Post]: https://openai.com/research/better-language-models\n[GitHub Copilot]: https://github.com/features/copilot/\n[GPT-4 and GPT-4 Turbo]: https://platform.openai.com/docs/models/gpt-4-and-gpt-4-turbo\n[GPT3 Apps Blog Post]: https://openai.com/blog/gpt-3-apps/\n[OpenAI Examples]: https://platform.openai.com/examples"""

class Actives(BaseModel):
    original_sentence: str = Field(..., description="The original sentence from the article that violates one or more rules of the custom style guide.")
    revised_sentence: str = Field(..., description="The revised sentence with no violations.")
    clear_explanation: str = Field(..., description="A clear explanation of the revision.")

class SmartEditorResponse(BaseModel):
    violations: List[Actives] = Field(..., description="A list of all instances of sentences from the article that violates one or more rules of the custom style guide.")


class ExtendedSmartEditorResponse(SmartEditorResponse):
    run_url: Optional[str] = Field(None, description="LangSmith trace URL.")

    class Config:
        schema_extra = {
            "example": {
                "violations":[
                    {
                        "original_sentence": "The magic of large language models is that by being trained to minimize this prediction error over vast quantities of text, the models end up learning concepts useful for these predictions.",
                        "revised_sentence": "The magic of large language models lies in their training to minimize prediction error over vast quantities of text, which leads them to learn concepts useful for these predictions.",
                        "clear_explanation": "The revision changes the sentence to active voice by removing the passive construction 'by being trained' and replacing it with an active construction 'lies in their training'. Fixes: [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    },
                    {
                        "original_sentence": "Large language models can be prompted to produce output in a few ways:",
                        "revised_sentence": "You can prompt large language models to produce output in a few ways:",
                        "clear_explanation": "The revision changes the sentence to active voice by specifying the actor ('You') who can prompt the models, instead of the passive 'can be prompted'. Fixes: [Use the present tense whenever possible.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-present-tense), [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    },
                    {
                        "original_sentence": "Write your instruction at the top of the prompt (or at the bottom, or both), and the model will do its best to follow the instruction and then stop.",
                        "revised_sentence": "Write your instruction at the top of the prompt (or at the bottom, or both), and the model does its best to follow the instruction and then stops.",
                        "clear_explanation": "The revision changes the sentence to present tense by replacing 'will do' with 'does' and 'will stop' with 'stops'. Fixes: [Use the present tense whenever possible.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-present-tense)"
                    },
                    {
                        "original_sentence": "To steer the model, try beginning a pattern or sentence that will be completed by the output you want to see.",
                        "revised_sentence": "To steer the model, begin a pattern or sentence that the output you want to see completes.",
                        "clear_explanation": "The revision changes the sentence to present tense and active voice by replacing 'try beginning' with 'begin' and rephrasing 'that will be completed by the output' to 'that the output completes'. Fixes: [Use the present tense whenever possible.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-present-tense), [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    },
                    {
                        "original_sentence": "In addition, the models won't necessarily know where to stop, so you will often need stop sequences or post-processing to cut off text generated beyond the desired output.",
                        "revised_sentence": "In addition, the models don't necessarily know where to stop, so you often need stop sequences or post-processing to cut off text generated beyond the desired output.",
                        "clear_explanation": "The revision changes the sentence to present tense by replacing 'won't' with 'don't' and 'will often need' with 'often need'. Fixes: [Use the present tense whenever possible.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-present-tense)"
                    },
                    {
                        "original_sentence": "Instructions can be detailed, so don't be afraid to write a paragraph explicitly detailing the output you want, just stay aware of how many [tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them) the model can process.",
                        "revised_sentence": "You can detail instructions, so don't be afraid to write a paragraph that explicitly details the output you want, just stay aware of how many [tokens](https://help.openai.com/en/articles/4936856-what-are-tokens-and-how-to-count-them) the model can process.",
                        "clear_explanation": "The revision changes the sentence to active voice by rephrasing 'Instructions can be detailed' to 'You can detail instructions'. Fixes: [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    },
                    {
                        "original_sentence": "** Explicitly asking the model to produce high quality output or output as if it was written by an expert can induce the model to give higher quality answers that it thinks an expert would write.",
                        "revised_sentence": "** Explicitly asking the model to produce high quality output or output as if an expert wrote it can induce the model to give higher quality answers that it thinks an expert would write.",
                        "clear_explanation": "The revision changes the sentence to active voice by rephrasing 'as if it was written by an expert' to 'as if an expert wrote it'. Fixes: [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    },
                    {
                        "original_sentence": "This can be done by simply adding a line like \"[Let's think step by step](https://arxiv.org/abs/2205.11916)\" before each answer.",
                        "revised_sentence": "You can simply add a line like \"[Let's think step by step](https://arxiv.org/abs/2205.11916)\" before each answer to achieve this.",
                        "clear_explanation": "The revision changes the sentence to active voice by specifying the actor ('You') who can add the line, instead of the passive 'can be done'. Fixes: [Use the active voice.](https://github.com/OutSystems/docs-validation/blob/master/style-guide/content.adoc#use-the-active-voice)"
                    }
                ],
                "run_url":"https://smith.langchain.com/public/74ac02bf-2361-4f64-85a3-4bc05d75278a/r"
            }
        }


class SmartEditorRequest(BaseModel):
    text: str = Field(..., description="Text.", example=SmartEditorRequest_text_example)


class ErrorResponse(BaseModel):
    error: str = Field(..., description="A brief description of the error.")
    message: str = Field(..., description="A more detailed explanation of the error.")
    status_code: int = Field(..., description="The HTTP status code associated with the error.")


def handle_endpoint_error(e: Exception):
    logging.error(f"An error occurred: {str(e)}")
    error_response = ErrorResponse(
        error="Server Error",
        message="An internal error occurred. Please try again later.",
        status_code=500
    )
    raise HTTPException(
        status_code=500,
        detail=error_response.dict()
    )