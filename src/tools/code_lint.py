import subprocess

def code_lint(code: str) -> Dict:
    """Run pylint on code."""
    result = subprocess.run(["pylint", "--disable=C,R,W", "-f", "json"], 
                           input=code, text=True, capture_output=True)
    return {
        "valid": result.returncode == 0,
        "errors": result.stdout
    }