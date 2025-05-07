import json
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from datetime import datetime
import time
import schedule
import pymongo
import uuid

# MongoDB connection setup
MONGO_URI = "mongodb://localhost:27017"
DATABASE_NAME = "Money_control"
COLLECTION_NAME = "myNewCollection1"

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

def scrape_nse_data():
    # Configure Microsoft Edge options
    options = Options()
    options.headless = False  # Set to True for invisible browser
    options.add_argument("--disable-blink-features=AutomationControlled")

    # Initialize Edge WebDriver
    driver = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()), options=options)

    try:
        # Open NSE India page
        nse_url = "https://www.nseindia.com/market-data/live-equity-market?symbol=NIFTY%2050"
        driver.get(nse_url)
        time.sleep(10)  # Allow time for page to load

        rows = driver.find_elements("xpath", "//table//tr")

        expected_num_cells = 14

        # Build a single dictionary for all companies
        companies_data = {}

        for row in rows[1:]:  # Skip header row
            cells = row.find_elements("tag name", "td")
            if cells and len(cells) >= expected_num_cells:
                company_name = cells[0].text.strip()
                company_data = {
                    "Open": cells[1].text.strip(),
                    "High": cells[2].text.strip(),
                    "Low": cells[3].text.strip(),
                    "PREV. CLOSE": cells[4].text.strip(),
                    "LTP": cells[5].text.strip(),
                    "Indicative Close": cells[6].text.strip(),
                    "Change": cells[7].text.strip(),
                    "% Change": cells[8].text.strip(),
                    "Volume (shares)": cells[9].text.strip(),
                    "Value (₹ Crores)": cells[10].text.strip(),
                    "52W High": cells[11].text.strip(),
                    "52W Low": cells[12].text.strip(),
                    "30 d % Change": cells[13].text.strip()
                }
                companies_data[company_name] = company_data
            else:
                print(f"Skipping row due to unexpected number of cells: {len(cells)}")

        # Create the nested structure matching the synthetic data generator
        nested_data = [
            {
                "_id": str(uuid.uuid4()),  # Generate a unique ID for the nested object
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "companies": companies_data
            }
        ]

        # Final document to insert
        final_document = {
            "data": nested_data
        }

        if companies_data:
            result = collection.insert_one(final_document)
            print(f"Data successfully saved to MongoDB with ID: {result.inserted_id}")
        else:
            print("No company data found to save.")

    except Exception as e:
        print(f"Error during scraping: {str(e)}")
    finally:
        driver.quit()

# Schedule the scraper to run every 1 minute (for testing, adjust as needed)
schedule.every(1).minutes.do(scrape_nse_data)

print("Scheduler started. Press Ctrl+C to stop.")
while True:
    schedule.run_pending()
    time.sleep(1)