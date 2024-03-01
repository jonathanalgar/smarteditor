import argparse
import json
import logging
import logging.config
import os
import ssl
from pathlib import Path

import uvicorn
from fastapi import Body, Depends, FastAPI, HTTPException, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader

from preprocessing import is_valid_notebook, keep_only_markdown_cells
from schema import (ErrorResponse, ExtendedSmartEditorResponse,
                    SmartEditorRequest, handle_endpoint_error)
from smarteditor import smarteditor
from vale_processing import append_violation_fixes, process_with_vale

# --------------------------------
# Configuration and initialization
# --------------------------------

app = FastAPI(
    title="smarteditor",
    description="Service to ingest text and batch transform sentences that violate style rules using Vale output as input to an LLM (currently `gpt-4-1106-preview`).",
    version="0.2",
    cookies_secure=True
)

with open('config.json') as f:
    config = json.load(f)

logging.basicConfig(
    level=config['logging']['level'],
    format=config['logging']['format'],
    datefmt=config['logging']['datefmt']
)

# Command-line arguments for SSL and server configuration
parser = argparse.ArgumentParser(description="Run a FastAPI server with SSL")
parser.add_argument("--certfile", type=str, required=True, help="Path to the SSL certificate file")
parser.add_argument("--keyfile", type=str, required=True, help="Path to the private key file associated with the SSL certificate")
parser.add_argument("--host", type=str, default="localhost", help="Host to bind the service to")
parser.add_argument("--port", type=int, default=9006, help="Port to bind the service to")

args = parser.parse_args()

# --------------------------------
# Authentication and middleware
# --------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=config['cors']['config']['allow_origins'],
    allow_credentials=config['cors']['config']['allow_credentials'],
    allow_methods=config['cors']['config']['allow_methods'],
    allow_headers=config['cors']['config']['allow_headers'],
    expose_headers=config['cors']['config']['expose_headers'],
)


@app.middleware("http")
async def secure_headers(request: Request, call_next):
    response = await call_next(request)
    for header, value in config['security']['headers'].items():
        response.headers[header] = value
    return response

API_KEY_NAME = "X-API-Token"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False, description='API key required for authorization')


async def get_api_key(api_key: str = Security(api_key_header)):
    """
    Security dependency to validate the API key provided by the client.

    Args:
        api_key (str): API key provided in the request headers.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the provided API key does not match the expected value.
    """
    correct_api_key = os.getenv("SMARTEDITOR_TOKEN")
    if api_key != correct_api_key:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    return api_key

# --------------------------------
# Route
# --------------------------------


@app.post(
    "/smarteditor",
    response_model=ExtendedSmartEditorResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation Error"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"}
    }
)
def smarteditor_text(
    request: SmartEditorRequest = Body(...),
    token: str = Depends(get_api_key)
):
    """Endpoint to process smarteditor requests."""
    try:
        text = request.text

        # Preprocessing
        if (is_valid_notebook(text)):
            text = keep_only_markdown_cells(text)

        # Extract sentences using Vale
        sentences_with_violations, unique_checks = process_with_vale(text)

        if not sentences_with_violations:
            return ExtendedSmartEditorResponse(violations=[], run_url=None)

        # Send to LLM
        active_response, run_url = smarteditor(text, sentences_with_violations)
        if active_response is None:
            raise Exception("Failed to generate transformed sentences.")

        # Append links to explanations
        append_violation_fixes(active_response.violations, sentences_with_violations, unique_checks)

        # Filter out unchanged sentences
        total_violations_before = len(active_response.violations)

        filtered_violations = [
            violation for violation in active_response.violations
            if violation.original_sentence.strip() != violation.revised_sentence.strip()
        ]

        violations_removed = total_violations_before - len(filtered_violations)
        logging.debug(f"Violations removed because they were unchanged: {violations_removed}")

        return ExtendedSmartEditorResponse(violations=filtered_violations, run_url=run_url)

    except Exception as e:
        handle_endpoint_error(e)

# --------------------------------
# Check files and run service
# --------------------------------


def check_file_exists(file_path: str, file_type: str):
    """Ensures the SSL certificate and key files exist."""
    if not Path(file_path).exists():
        error_message = f"{file_type} '{file_path}' does not exist."
        logging.error(error_message)
        raise SystemExit(1)


if __name__ == "__main__":
    check_file_exists(args.certfile, "SSL certificate file")
    check_file_exists(args.keyfile, "Private key file")

    CERT_FILE = args.certfile
    KEY_FILE = args.keyfile

    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.load_cert_chain(os.path.expanduser(CERT_FILE), keyfile=os.path.expanduser(KEY_FILE))

    # Run the Uvicorn server with SSL configuration
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        ssl_certfile=os.path.expanduser(CERT_FILE),
        ssl_keyfile=os.path.expanduser(KEY_FILE),
    )
