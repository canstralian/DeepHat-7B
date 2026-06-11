import os
import json
from typing import Dict, Any
from src.tools import (
    dataset_search, 
    model_registry_lookup, 
    cve_lookup,
    code_lint,
    code_test,
    policy_check,
    artifact_store,
    eval_runner
)

class SecurityAgent:
    def __init__(self):
        self.tools = {
            "dataset_search": dataset_search,
            "model_registry_lookup": model_registry_lookup,
            "cve_lookup": cve_lookup,
            "code_lint": code_lint,
            "code_test": code_test,
            "policy_check": policy_check,
            "artifact_store": artifact_store,
            "eval_runner": eval_runner
        }
        self.audit_log = []

    def generate(self, prompt: str) -> str:
        """Process a prompt through the agent pipeline."""
        # Policy check
        policy_result = self.tools["policy_check"](prompt)
        if not policy_result["allowed"]:
            self.audit_log.append({
                "timestamp": time.time(),
                "user_intent": prompt,
                "tool": "policy_check",
                "outcome": "rejected",
                "reason": policy_result["reason"]
            })
            return f"Refused: {policy_result['reason']}"

        # Retrieve context
        context = self.tools["dataset_search"](prompt)
        
        # Generate code
        response = self.tools["model_registry_lookup"](
            prompt=prompt,
            context=context
        )
        
        # Validate code
        lint_result = self.tools["code_lint"](response)
        if not lint_result["valid"]:
            response += f"\nLINTING ISSUE: {lint_result['errors']}"
        
        # Store artifact
        self.tools["artifact_store"]({
            "prompt": prompt,
            "response": response,
            "audit_log": self.audit_log
        })
        
        return response

    def evaluate(self, prompt: str, expected: str) -> Dict[str, Any]:
        """Run evaluation cases."""
        return self.tools["eval_runner"](prompt, expected)