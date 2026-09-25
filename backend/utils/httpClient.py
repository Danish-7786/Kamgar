import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def create_session():
    retry_policy = Retry(
        total = 3,
        backoff_factor =1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods = ["GET"],
        respect_retry_after_header = True,
        raise_on_status = False,
        
    )
    session = requests.Session()
    session.mount(
        "https://",
        HTTPAdapter(max_retries=retry_policy),
    
    )
    return session

def fetch_jobs(session, url, params= None):
    response = session.get(
        url,
        params= params,
        timeout = (5,30),
        
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict) or not isinstance(data.get("jobs"),list):
        raise ValueError("Expected a JSON object containing a jobs list")
    return data["jobs"]
