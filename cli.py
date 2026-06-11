#!/usr/bin/env python3
"""Command-line interface for DeepHat security assistance."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.agent import DeepHatAgent, SecurityAssistantAgent
from src.presets import SYSTEM_PRESETS
from src.utils import build_messages


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DeepHat 7B CLI")
    parser.add_argument("prompt", nargs="?", help="Prompt text")
    parser.add_argument("--model", default="DeepHat/DeepHat-V1-7B", help="Hugging Face model ID")
    parser.add_argument("--preset", choices=list(SYSTEM_PRESETS), default="default", help="System preset")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Maximum new tokens")
    parser.add_argument("--top-p", type=float, default=0.9, help="Nucleus sampling top-p")
    parser.add_argument("--device", default="auto", help="Device map: auto, cpu, cuda, cuda:0")
    parser.add_argument("--load-in-4bit", action="store_true", help="Enable 4-bit quantized loading")
    parser.add_argument("--file", "-f", type=Path, help="Read prompt from a file")
    parser.add_argument("--output", "-o", type=Path, help="Write response to a file")
    parser.add_argument(
        "--local-triage",
        action="store_true",
        help="Use deterministic local triage tools instead of model inference",
    )
    return parser.parse_args()


def read_prompt(args: argparse.Namespace) -> str:
    if args.file:
        return args.file.read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return input("Prompt: ")


def main() -> int:
    args = parse_args()
    prompt = read_prompt(args).strip()
    if not prompt:
        print("No prompt provided.", file=sys.stderr)
        return 2

    if args.local_triage:
        response = SecurityAssistantAgent().respond(prompt, "auto")
    else:
        messages = build_messages(SYSTEM_PRESETS[args.preset], [], prompt)
        agent = DeepHatAgent(
            model_id=args.model,
            device=args.device,
            load_in_4bit=args.load_in_4bit,
        )
        response = agent.generate(
            messages=messages,
            temperature=args.temperature,
            max_new_tokens=args.max_tokens,
            top_p=args.top_p,
        )

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(response + "\n", encoding="utf-8")
    else:
        print(response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
