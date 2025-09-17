from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

app = FastAPI()

SCAN_CLAUSE = """( {cash} (
    monthly close > monthly upper bollinger band( 20 , 1.5 )
    and weekly close > weekly upper bollinger band( 20 , 1.5 )
    and daily close > daily upper bollinger band( 20 , 1.5 )
    and daily close > daily open * 1.03
    and daily close > [0] 1 hour vwap
    and daily close > [0] 15 minute vwap
    and daily close > [0] 5 minute upper bollinger band( 20 , 1.5 )
    and daily close > [0] 5 minute vwap
    and market cap > 1000 ) )"""

def fetch_chartink_results(scan_clause: str):
    with requests.Session() as s:
        home_resp = s.get("https://chartink.com/screener")
        soup = BeautifulSoup(home_resp.text, "lxml")
        meta = soup.find("meta", {"name": "csrf-token"})
        csrf_token = meta["content"] if meta else s.cookies.get("XSRF-TOKEN")
        headers = {"x-requested-with": "XMLHttpRequest","x-csrf-token": csrf_token}
        payload = {"scan_clause": scan_clause}
        resp = s.post("https://chartink.com/screener/process",
                      headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json().get("data", [])

class ScanClause(BaseModel):
    scan_clause: str = SCAN_CLAUSE

@app.post("/scan")
def run_scan(payload: ScanClause):
    results = fetch_chartink_results(payload.scan_clause)
    return {"count": len(results), "results": results}
