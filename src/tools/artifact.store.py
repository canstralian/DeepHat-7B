import os
import json
import datetime

def artifact_store(data: Dict) -> None:
    """Store artifacts in logs."""
    timestamp = datetime.datetime.now().isoformat()
    filename = f"logs/{timestamp}.json"
    
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "w") as f:
        json.dump(data, f)