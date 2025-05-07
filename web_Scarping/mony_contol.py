from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from bs4 import BeautifulSoup
import pymongo
import schedule
import time
import random
from datetime import datetime

# MongoDB connection details
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "Money_control"
COLLECTION_NAME = "NEWS_DATA"

client = pymongo.MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

BASE_URL = "https://www.moneycontrol.com/news/business"
SECTIONS = {
    "business": "",
    "markets": "markets",
    "stocks": "stocks",
    "economy": "economy",
    "companies": "companies",
    "trends": "trends",
    "ipo": "ipo",
    "opinion": "tags/opinion.html"
}

# Setup Selenium options (headless Chrome)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run browser in background
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("window-size=1920,1080")
chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Initialize WebDriver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def scrape_and_save():
    news_data = {section: [] for section in SECTIONS}

    for section_name, section_path in SECTIONS.items():
        url = f"{BASE_URL}/{section_path}" if section_path else BASE_URL
        print(f"Scraping {section_name}: {url}")

        # simulate human browsing delay
        time.sleep(random.uniform(3, 7))

        try:
            driver.get(url)
            time.sleep(random.uniform(3, 6))  # Let the page load properly
            page_source = driver.page_source
        except Exception as e:
            print(f"  → Failed to fetch {section_name}: {e}")
            continue

        soup = BeautifulSoup(page_source, "html.parser")

        ul = soup.find("ul", id="cagetory") or soup.find("ul", id="category")
        if not ul:
            print(f"  → No <ul id='cagetory'> or 'category' found for {section_name}")
            continue

        headlines = []
        for li in ul.find_all("li", class_="clearfix"):
            link_tag = li.find("h2")
            if link_tag and link_tag.find("a"):
                a = link_tag.find("a")
            else:
                a = li.find("a")

            if not a or not a.get("href"):
                continue

            title = a.get_text(strip=True)
            link  = a["href"]
            if link.startswith("/"):
                link = f"https://www.moneycontrol.com{link}"

            if title:
                headlines.append({"title": title, "link": link})

        print(f"  → Found {len(headlines)} items in {section_name}")
        news_data[section_name] = headlines

    # Add timestamp and insert into MongoDB
    news_data["scrape_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    collection.insert_one(news_data)
    print("Data saved to MongoDB\n")

# Schedule to run every minute at :00 seconds
schedule.every().minute.at(":00").do(scrape_and_save)

print("Scheduler started. Press Ctrl+C to stop.")
try:
    while True:
        schedule.run_pending()
        time.sleep(1)
except KeyboardInterrupt:
    print("Scheduler stopped by user.")
finally:
    driver.quit()
