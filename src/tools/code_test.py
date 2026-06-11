import subprocess

def code_test(code: str, test_cases: List[str]) -> Dict:
    """Run unit tests in sandbox."""
    # Write code to temp file
    with open("temp_test.py", "w") as f:
        f.write(code)
    
    # Run tests
    cmd = ["python", "-m", "pytest", "temp_test.py", "-v"]
    result = subprocess.run(cmd, capture_output=True)
    
    return {
        "passed": result.returncode == 0,
        "output": result.stdout.decode()
    }