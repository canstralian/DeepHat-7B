def policy_check(prompt: str) -> Dict:
    """Check prompt against safety policy."""
    harmful_keywords = [
        "malware", "exploit", "phishing", "steal cookies",
        "persistence", "bypass", "destructive"
    ]
    
    for keyword in harmful_keywords:
        if keyword in prompt.lower():
            return {
                "allowed": False,
                "reason": f"Contains prohibited term: {keyword}"
            }
    
    return {"allowed": True}