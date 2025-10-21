from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# FastAPI setup
app = FastAPI()

# Request schema
class CurrencyRequest(BaseModel):
    from_currency: str
    to_currency: str

# Selenium setup (update path as needed)
chrome_driver_path = r"C:\WebDrivers\chromedriver.exe"
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
chrome_options.add_experimental_option('useAutomationExtension', False)

def get_frankfurter_rate(base, target):
    try:
        url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
        response = requests.get(url, timeout=10, verify=False)
        response.raise_for_status()
        data = response.json()
        if "rates" in data and target in data["rates"]:
            return data["rates"][target]
        else:
            return None
    except Exception as e:
        return None

def get_from_xrates(base, target):
    try:
        url = f"https://www.x-rates.com/calculator/?from={base}&to={target}&amount=1"
        res = requests.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, "html.parser")
        rate_text = soup.find("span", class_="ccOutputTrail").previous_sibling
        return float(rate_text.strip())
    except Exception as e:
        return None

def get_from_investing(base, target, driver):
    try:
        url = f"https://www.investing.com/currencies/{base.lower()}-{target.lower()}"
        driver.get(url)
        rate_element = WebDriverWait(driver, 12).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-test="instrument-price-last"]'))
        )
        rate_text = rate_element.text.strip().replace(",", "")
        return float(rate_text)
    except Exception as e:
        return None

def get_all_rates(base, target):
    results = {}
    results["frankfurter.app"] = get_frankfurter_rate(base, target)
    results["x-rates.com"] = get_from_xrates(base, target)
    # Selenium driver for dynamic sites
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    results["investing.com"] = get_from_investing(base, target, driver)
    driver.quit()
    return results

@app.post("/get-rate")
def get_rate(req: CurrencyRequest) -> Dict[str, Optional[float]]:
    base = req.from_currency.strip().upper()
    target = req.to_currency.strip().upper()
    rates = get_all_rates(base, target)
    return rates
