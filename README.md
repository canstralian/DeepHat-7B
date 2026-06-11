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

# DeepHat 7B Security Assistant

Gradio app and workflow toolkit for DeepHat-style cybersecurity assistance. The app combines model-backed chat with deterministic local triage tools for CVE lookup, static code checks, policy coverage checks, artifact export, and lightweight evaluations.

Use this only on systems you own or have explicit authorization to assess. Model output must be verified against source evidence and current advisories before operational use.

## Features

- Chat UI with conversation history, mode presets, generation controls, quick examples, and conversation export.
- Lazy model loading through `DeepHatAgent`, so imports and tests do not download model weights.
- Safe fallback to local deterministic triage if model inference is unavailable.
- CLI for local prompt execution with optional local-triage mode.
- API client for a running Gradio app.
- Batch and CI security-scan scripts that default to static checks instead of loading a 7B model.
- GitHub Actions CI and Hugging Face Space publish workflows.

## Project Structure

```text
.
|-- app.py
|-- api_client.py
|-- cli.py
|-- requirements.txt
|-- scripts/
|   `-- publish_to_hf.py
|-- src/
|   |-- agent.py
|   |-- presets.py
|   |-- tools/
|   `-- utils/
|-- workflows/
|   |-- batch_scan.py
|   `-- ci_integration.py
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

## CLI Usage

```powershell
python cli.py --local-triage "What is CVE-2021-44228?"
python cli.py --preset code_review --file .\example.py --output .\outputs\review.md
python workflows\batch_scan.py --dir .\src --output .\outputs\scan_results.json
python workflows\ci_integration.py
```

`--local-triage` uses deterministic tools and does not load the model.

## API Client

```python
from api_client import DeepHatClient

client = DeepHatClient("http://localhost:7860")
print(client.chat("Explain SQL injection prevention techniques", preset="code_review"))
```

## Configuration

Environment variables:

- `MODEL_ID`: model loaded by `DeepHatAgent` and `model_registry_lookup` (`DeepHat/DeepHat-V1-7B` by default).
- `DEVICE`: model device map (`auto`, `cpu`, `cuda`, `cuda:0`).
- `USE_4BIT`: set to `true` to request 4-bit loading.
- `MAX_NEW_TOKENS`: default token cap for `model_registry_lookup`.
- `DO_SAMPLE`: set to `true` for sampling in `model_registry_lookup`.
- `SECURITY_ASSISTANT_TITLE`: overrides the Gradio app title.
- `SECURITY_ASSISTANT_ARTIFACT_DIR`: overrides export and artifact output location.
- `HF_TOKEN`: required by `scripts/publish_to_hf.py` and the publish workflow.

## Modes

- `default`: bounded general cybersecurity assistance.
- `offensive`: authorized testing planning with scope and safety constraints.
- `defensive`: hardening, detection, response, and recovery.
- `code_review`: secure code analysis with remediation guidance.
- `malware`: safe malware-analysis support and detection ideas.
- `compliance`: control mapping, evidence, gaps, and next steps.
- `api_security`: OWASP API risks, auth, rate limits, REST, and GraphQL.

## Hardware Notes

| Mode | Approximate requirement |
| --- | --- |
| BF16/full precision | 16 GB+ VRAM recommended |
| 4-bit loading | 8 GB+ VRAM and compatible bitsandbytes stack |
| CPU | 32 GB+ RAM recommended; slow for interactive use |
| Local triage | No model or GPU required |

## Validation

```powershell
python -m compileall app.py api_client.py cli.py src evals tests scripts workflows
python -m pytest
python workflows\ci_integration.py
```

The bundled CI workflow installs only `pytest` for fast import and unit tests. It intentionally does not download DeepHat model weights.

## Publishing

`.github/workflows/publish.yml` publishes the repository to the Hugging Face Space configured by `HF_SPACE_ID` after tests pass. Configure `HF_TOKEN` as a GitHub Actions secret before relying on automatic deployment.
