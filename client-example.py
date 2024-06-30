import argparse
import getpass
import json
import logging
import os
from datetime import datetime

import requests

logging.basicConfig(level=logging.INFO,
                    format='%(levelname)s [%(asctime)s] %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S')


def log_full_payload(md_content):
    payload = {
        "text": md_content
    }
    logging.info("Payload:")
    logging.info(json.dumps(payload, indent=2))


def send_text_to_api(md_content, url, token, verify_ssl=True):
    log_full_payload(md_content)

    actual_payload = json.dumps({
        "text": md_content
    })

    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Token": token
    }

    logging.info("Sending payload...")
    try:
        response = requests.post(url, headers=headers, data=actual_payload, timeout=240, verify=verify_ssl)
        response.raise_for_status()  # Raises an HTTPError for bad responses
    except requests.exceptions.SSLError as ssl_err:
        if verify_ssl:
            logging.error(f"SSL Error occurred: {ssl_err}")
            raise  # Re-raise the exception if SSL verification is enabled
        else:
            logging.warning("SSL verification is disabled. Proceeding with insecure request.")
            response = requests.post(url, headers=headers, data=actual_payload, timeout=240, verify=False)
            response.raise_for_status()
    except requests.exceptions.RequestException as req_err:
        logging.error(f"An error occurred while sending the request: {req_err}")
        raise  # Re-raise the exception to maintain original error behavior

    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    logging.info(f"Response received at {timestamp}")

    return response.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send text to the API")
    parser.add_argument("md_file_path", help="Path to file containing markdown formatted text.")
    parser.add_argument("--no-verify-ssl", action="store_true", help="Disable SSL certificate verification")

    args = parser.parse_args()

    # Check for environment variables
    url = os.getenv("SMARTEDITOR_CLIENT_EXAMPLE_URL")
    token = os.getenv("SMARTEDITOR_CLIENT_EXAMPLE_TOKEN")

    if not url:
        url = getpass.getpass(prompt="Enter endpoint URL (eg. https://smarteditor-prod.westeurope.cloudapp.azure.com:9100/smarteditor): ")
    if not token:
        token = getpass.getpass(prompt="Enter SMARTEDITOR_TOKEN: ")

    with open(args.md_file_path, 'r') as file:
        md_content = file.read()
    logging.info("File read successfully.")

    verify_ssl = not args.no_verify_ssl
    try:
        response = send_text_to_api(md_content, url, token, verify_ssl)
        print(response)
    except requests.exceptions.RequestException as e:
        logging.error(f"Error occurred: {e}")
        print(f"Failed to get a response from the server: {e}")