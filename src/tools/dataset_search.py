import requests
from typing import List, Dict

def dataset_search(query: str) -> List[Dict]:
    """Search approved datasets."""
    # Mock API call
    response = requests.get(f"https://huggingface.co/api/datasets?q={query}")
    return [{"id": d["id"], "license": d["license"]} for d in response.json()]