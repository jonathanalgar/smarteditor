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


def send_text_to_api(md_content, url, token):
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
    response = requests.post(url, headers=headers, data=actual_payload, timeout=240)

    timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    logging.info(f"Response received at {timestamp}")

    return response.text


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send text to the API")
    parser.add_argument("md_file_path", help="Path to file containing markdown formatted text.")

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

    response = send_text_to_api(md_content, url, token)
    print(response)
