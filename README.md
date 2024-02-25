# smarteditor

![ci](https://github.com/jonathanalgar/activator/actions/workflows/build-docker.yml/badge.svg) [![Bugs](https://sonarcloud.io/api/project_badges/measure?project=jonathanalgar_activator&metric=bugs)](https://sonarcloud.io/summary/new_code?id=jonathanalgar_activator) [![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=jonathanalgar_activator&metric=vulnerabilities)](https://sonarcloud.io/summary/new_code?id=jonathanalgar_activator) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com) ![License: GPLv3](https://img.shields.io/badge/license-GPLv3-blue) [![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://makeapullrequest.com)

## Overview

[![Diagram of the system architecture of the smarteditor microservice, showing its integration with GitHub client](smarteditor-diag.png "Smarteditor Architecture Diagram")](https://jonathanalgar.github.io/slides/Using%20AI%20and%20LLMs%20in%20docs-as-code%20pipelines.pdf)

Service to batch transform sentences using Vale output as input to an LLM (currently `gpt-4-1106-preview`).

Exists to abstract interaction with the LLM and LangSmith APIs and provide a single interface for clients, for example [smarteditor-ghclient](https://github.com/jonathanalgar/smarteditor-ghclient).

See OpenAPI specification for the service [here](https://app.swaggerhub.com/apis/JONATHANALGARGITHUB/smarteditor/0.1).

## Usage

1. Clone the repo.
1. Copy `.env-example` to `.env` and fill in the required env variables.
1. Copy `.vale.ini-example` to `.vale.ini` add styles as required. Vale styles are located in the styles folder and require a `description` field. You can add a `link` field if you want to link out to the rule. To use `smarteditor` as `activator`, just use the one style:

    ```bash
    [*.*]
    Microsoft.Passive = warning
    ```

1. Optionally edit `config.json` to customize CORS and logging.
1. Run `docker-compose up` (v1) or `docker compose up` (v2) to build and start the service.
1. Run `python client-example.py example/how_to_work_with_large_language_models.md` to test. Expected output:

    ```bash
    x
    ```

1. This is a very basic client. Check [smarteditor-ghclient](https://github.com/jonathanalgar/smarteditor-ghclient) to integrate the service into your docs-as-code pipeline.

## Features

* Uses [LangChain's implementation of OpenAI function calling](https://python.langchain.com/docs/modules/model_io/output_parsers/types/pydantic) to reliably generate a JSON of expected format.
* Optionally integrates with LangSmith to serve [trace URL](https://api.python.langchain.com/en/latest/chains/langchain.chains.openai_functions.base.create_structured_output_chain.html#) for each generation.

## TODO

- [ ] Better error handling
- [ ] Unit tests
- [ ] Special handling for large files
- [ ] Rate limiting at the service level
- [ ] Explore extending to models beyond OpenAI
- [X] Option to use Azure OpenAI Services
