from pathlib import Path
from unittest.mock import patch

from api_client import _extract_response
from src.agent import DeepHatAgent, SecurityAgent, SecurityAssistantAgent
from src.tools.artifact_store import store_artifact
from src.tools.code_test import analyze_python_code
from src.tools.eval_runner import run_evals
from src.tools.model_registry_lookup import model_registry_lookup
from src.utils import export_chat
from workflows.ci_integration import ci_scan


def test_agent_routes_cve_lookup() -> None:
    agent = SecurityAssistantAgent()

    response = agent.respond("What is CVE-2021-44228?", "auto")

    assert "`cve_lookup`" in response
    assert "Log4Shell" in response


def test_code_lint_reports_shell_true() -> None:
    agent = SecurityAssistantAgent()

    response = agent.respond(
        "```python\nimport subprocess\nsubprocess.run(user_input, shell=True)\n```",
        "code_lint",
    )

    assert "`code_lint`" in response
    assert "shell-true" in response
    assert "shell=True" in response


def test_code_test_parses_without_execution() -> None:
    result = analyze_python_code("def test_example():\n    assert True\n")

    assert result.syntax_ok is True
    assert result.test_function_count == 1


def test_policy_check_is_default_fallback() -> None:
    agent = SecurityAssistantAgent()

    response = agent.respond("Deployments require peer review and rollback planning.", "auto")

    assert "`policy_check`" in response
    assert "Change Control" in response


def test_artifact_store_writes_to_configured_directory(tmp_path: Path) -> None:
    artifact = store_artifact("review note", base_dir=tmp_path)

    path = Path(artifact.path)
    assert path.parent == tmp_path
    assert path.read_text(encoding="utf-8") == "review note\n"


def test_eval_runner_uses_responder_contract() -> None:
    agent = SecurityAssistantAgent()

    results = run_evals(agent.respond)

    assert results
    assert all(result.passed for result in results)


def test_legacy_security_agent_alias() -> None:
    agent = SecurityAgent()

    response = agent.respond("What is CVE-2021-44228?", "auto")

    assert "Log4Shell" in response


def test_legacy_model_registry_lookup_wrapper() -> None:
    class FakeInputIds:
        shape = (1, 2)

    class FakeInputs(dict):
        def to(self, device: str) -> "FakeInputs":
            assert device == "cpu"
            return self

    class FakeTokenizer:
        eos_token_id = 0

        def __call__(self, prompt: str, return_tensors: str) -> FakeInputs:
            assert "Question: code model" in prompt
            assert return_tensors == "pt"
            return FakeInputs({"input_ids": FakeInputIds()})

        def decode(self, tokens: list[int], skip_special_tokens: bool) -> str:
            assert tokens == [3, 4]
            assert skip_special_tokens is True
            return "generated answer"

    class FakeModel:
        device = "cpu"

        def generate(self, **kwargs):
            assert kwargs["max_new_tokens"] == 256
            return [[1, 2, 3, 4]]

    with patch("src.tools.model_registry_lookup.load_model", return_value=(FakeTokenizer(), FakeModel())):
        response = model_registry_lookup("code model", [])

    assert response == "generated answer"


def test_deephat_fallback_prompt_formats_messages() -> None:
    prompt = DeepHatAgent._fallback_chat_prompt(
        [
            {"role": "system", "content": "Stay scoped."},
            {"role": "user", "content": "Review this code."},
        ]
    )

    assert "System: Stay scoped." in prompt
    assert "User: Review this code." in prompt
    assert prompt.endswith("Assistant:")


def test_export_chat_writes_markdown(tmp_path: Path) -> None:
    path = export_chat(
        [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "world"},
        ],
        "markdown",
        output_dir=tmp_path,
    )

    content = path.read_text(encoding="utf-8")
    assert path.suffix == ".md"
    assert "## User" in content
    assert "hello" in content


def test_api_client_extracts_last_message_content() -> None:
    response = _extract_response(
        [
            {"role": "user", "content": "question"},
            {"role": "assistant", "content": "answer"},
        ]
    )

    assert response == "answer"


def test_ci_integration_reports_high_findings(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "bad.py"
    source.write_text("import subprocess\nsubprocess.run(user_input, shell=True)\n", encoding="utf-8")
    report = tmp_path / "report.json"

    monkeypatch.setenv("CHANGED_FILES", str(source))
    monkeypatch.setenv("SCAN_REPORT_PATH", str(report))

    exit_code = ci_scan()

    assert exit_code == 1
    assert "shell-true" in report.read_text(encoding="utf-8")
