---
title: DeepHat 7B
emoji: "🐢"
colorFrom: indigo
colorTo: green
sdk: gradio
sdk_version: 6.17.3
python_version: "3.12"
app_file: app.py
pinned: false
license: apache-2.0
hf_oauth: true
hf_oauth_scopes:
  - inference-api
---

# Security Assistant

Local Gradio app for security triage tasks. It routes prompts to tools for CVE lookup, dataset discovery, DeepHat model generation, static code checks, policy coverage checks, artifact storage, and local evaluation cases.

Most triage tools are deterministic and local. The `model_registry_lookup` tool lazily loads the configured Hugging Face model and may download model weights on first use. The app does not download malware samples or execute user-submitted code.

## Project Structure

```text
security-assistant/
|-- app.py
|-- requirements.txt
|-- src/
|   |-- agent.py
|   |-- tools/
|   `-- utils/
|-- evals/
`-- tests/
```

## Run Locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Then open the local Gradio URL printed by the server.

## Tooling

- `dataset_search`: searches a small local catalog of security datasets.
- `model_registry_lookup`: lazily loads `MODEL_ID` and generates a response with retrieved context.
- `cve_lookup`: looks up a small offline CVE catalog for deterministic demos.
- `code_lint`: applies static security regex checks without executing submitted code.
- `code_test`: parses Python syntax and test-like structure without executing submitted code.
- `policy_check`: checks policy text for common control coverage.
- `artifact_store`: writes Markdown notes to `outputs/artifacts`.
- `eval_runner`: runs local JSON evaluation cases from `evals/test_cases.json`.

## Configuration

Environment variables:

- `SECURITY_ASSISTANT_TITLE`: overrides the Gradio app title.
- `SECURITY_ASSISTANT_ARTIFACT_DIR`: overrides where `artifact_store` writes Markdown artifacts.
- `MODEL_ID`: overrides the model loaded by `model_registry_lookup` (`DeepHat/DeepHat-V1-7B` by default).
- `MAX_NEW_TOKENS`: controls generation length (`256` by default).
- `DO_SAMPLE`: set to `true` to enable sampling; deterministic generation is the default.

## Validate

```powershell
python -m compileall app.py src evals tests
python -m pytest
```

The local checks are narrow by design. Operational vulnerability findings should still be verified against authoritative, current sources.
