#!/usr/bin/env python3
"""Programmatic client for the DeepHat Gradio API."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class DeepHatClient:
    """Small wrapper around a running Gradio app."""

    def __init__(self, api_url: str) -> None:
        self.api_url = api_url.rstrip("/")

    def chat(
        self,
        message: str,
        preset: str = "default",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
    ) -> str:
        try:
            from gradio_client import Client
        except ImportError as exc:
            raise RuntimeError("Install gradio_client or requirements.txt to use api_client.py.") from exc

        client = Client(self.api_url)
        result = client.predict(
            message,
            [],
            "",
            preset,
            temperature,
            max_tokens,
            top_p,
            api_name="/chat",
        )
        return _extract_response(result)


def batch_process(input_path: Path, output_path: Path, api_url: str) -> None:
    client = DeepHatClient(api_url)
    prompts = [line.strip() for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    for index, prompt in enumerate(prompts, start=1):
        response = client.chat(prompt)
        results.append({"index": index, "prompt": prompt, "response": response})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2), encoding="utf-8")


def _extract_response(result: Any) -> str:
    if isinstance(result, list) and result:
        last = result[-1]
        if isinstance(last, dict):
            return str(last.get("content", ""))
        return str(last)
    return str(result)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DeepHat Gradio API client")
    parser.add_argument("--api-url", default="http://localhost:7860", help="Gradio app URL")
    parser.add_argument("--prompt", "-p", help="Single prompt")
    parser.add_argument("--batch", "-b", type=Path, help="Path to newline-delimited prompts")
    parser.add_argument("--output", "-o", type=Path, default=Path("outputs/api_results.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.batch:
        batch_process(args.batch, args.output, args.api_url)
        print(f"Results written to {args.output}")
        return 0

    client = DeepHatClient(args.api_url)
    if args.prompt:
        print(client.chat(args.prompt))
        return 0

    print("DeepHat interactive mode. Type 'quit' to exit.")
    while True:
        prompt = input("> ").strip()
        if prompt.lower() in {"quit", "exit", "q"}:
            return 0
        if prompt:
            print(client.chat(prompt))


if __name__ == "__main__":
    raise SystemExit(main())
