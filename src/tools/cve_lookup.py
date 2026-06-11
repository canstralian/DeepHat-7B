import requests

def cve_lookup(cve_id: str) -> Dict:
    """Get CVE info from NVD API."""
    url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?cveId={cve_id}"
    response = requests.get(url)
    return response.json()["vulnerabilities"][0]["cve"]