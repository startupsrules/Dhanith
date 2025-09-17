from flask import Flask, jsonify
from datetime import datetime
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

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
        home_resp.raise_for_status()
        soup = BeautifulSoup(home_resp.text, "lxml")
        meta = soup.find("meta", {"name": "csrf-token"})
        csrf_token = meta["content"] if meta else s.cookies.get("XSRF-TOKEN")
        headers = {"x-requested-with": "XMLHttpRequest", "x-csrf-token": csrf_token}
        payload = {"scan_clause": scan_clause}
        resp = s.post("https://chartink.com/screener/process", headers=headers, data=payload)
        resp.raise_for_status()
        return resp.json().get("data", [])

@app.route("/scan", methods=["GET"])
def scan():
    try:
        results = fetch_chartink_results(SCAN_CLAUSE)
        stocks = [{"nsecode": s["nsecode"], "name": s["name"]} for s in results]
        return jsonify({"count": len(results), "stocks": stocks})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
