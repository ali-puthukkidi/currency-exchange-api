from fastapi import FastAPI
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup

app = FastAPI()

class CurrencyRequest(BaseModel):
    from_currency: str
    to_currency: str

def get_frankfurter_rate(base, target):
    try:
        url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if "rates" in data and target in data["rates"]:
            return data["rates"][target]
        else:
            return None
    except Exception:
        return None

def get_from_xrates(base, target):
    try:
        url = f"https://www.x-rates.com/calculator/?from={base}&to={target}&amount=1"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rate_text = soup.find("span", class_="ccOutputTrail").previous_sibling
        return float(rate_text.strip())
    except Exception:
        return None

@app.post("/get-rate")
def get_rate(req: CurrencyRequest):
    base = req.from_currency.strip().upper()
    target = req.to_currency.strip().upper()
    rates = {
        "frankfurter.app": get_frankfurter_rate(base, target),
        "x-rates.com": get_from_xrates(base, target)
    }
    return rates
