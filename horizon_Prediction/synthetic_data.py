import json
import random
import datetime
import os
from uuid import uuid4
from datetime import timedelta

# List of NIFTY 50 companies
nifty_companies = [
    "NIFTY 50", "SBILIFE", "TECHM", "TCS", "INFY", "ULTRACEMCO", "HINDUNILVR", "GRASIM", 
    "INDUSINDBK", "ICICIBANK", "RELIANCE", "HDFCBANK", "ITC", "HCLTECH", "TITAN", 
    "HDFCLIFE", "WIPRO", "NESTLEIND", "LT", "TATACONSUM", "KOTAKBANK", "SUNPHARMA", 
    "M&M", "HINDALCO", "ONGC", "ASIANPAINT", "EICHERMOT", "BHARTIARTL", "CIPLA", 
    "COALINDIA", "SBIN", "HEROMOTOCO", "MARUTI", "TATASTEEL", "TATAMOTORS", "NTPC", 
    "JSWSTEEL", "BAJAJ-AUTO", "BAJFINANCE", "DRREDDY", "JIOFIN", "BEL", "BAJAJFINSV", 
    "POWERGRID", "APOLLOHOSP", "AXISBANK", "ETERNAL", "TRENT", "ADANIPORTS", "ADANIENT",
    "SHRIRAMFIN"
]

# Define base price ranges for each company
# Format: (min_price, max_price)
price_ranges = {
    "NIFTY 50": (23000, 25000),
    "SBILIFE": (1600, 1800),
    "TECHM": (1350, 1500),
    "TCS": (3400, 3600),
    "INFY": (1550, 1650),
    "ULTRACEMCO": (10000, 10500),
    "HINDUNILVR": (2750, 2850),
    "GRASIM": (2400, 2550),
    "INDUSINDBK": (1500, 1600),
    "ICICIBANK": (1130, 1180),
    "RELIANCE": (2900, 3050),
    "HDFCBANK": (1600, 1650),
    "ITC": (425, 450),
    "HCLTECH": (1350, 1410),
    "TITAN": (3200, 3300),
    "HDFCLIFE": (660, 690),
    "WIPRO": (480, 500),
    "NESTLEIND": (24300, 24900),
    "LT": (3400, 3500),
    "TATACONSUM": (1100, 1150),
    "KOTAKBANK": (1830, 1880),
    "SUNPHARMA": (1250, 1300),
    "M&M": (2400, 2480),
    "HINDALCO": (620, 650),
    "ONGC": (250, 265),
    "ASIANPAINT": (2950, 3030),
    "EICHERMOT": (4200, 4320),
    "BHARTIARTL": (1220, 1260),
    "CIPLA": (1350, 1390),
    "COALINDIA": (425, 440),
    "SBIN": (815, 840),
    "HEROMOTOCO": (4850, 4950),
    "MARUTI": (12300, 12550),
    "TATASTEEL": (150, 160),
    "TATAMOTORS": (970, 1010),
    "NTPC": (335, 350),
    "JSWSTEEL": (845, 870),
    "BAJAJ-AUTO": (8700, 8900),
    "BAJFINANCE": (6950, 7050),
    "DRREDDY": (5550, 5650),
    "JIOFIN": (270, 285),
    "BEL": (240, 250),
    "BAJAJFINSV": (1620, 1660),
    "POWERGRID": (285, 295),
    "APOLLOHOSP": (5800, 5950),
    "AXISBANK": (1050, 1100),
    "ETERNAL": (1800, 1850),
    "TRENT": (3600, 3700),
    "ADANIPORTS": (1175, 1225),
    "ADANIENT": (2900, 3000),
    "SHRIRAMFIN": (2400, 2500)
}

# Volume ranges for each company (in shares)
volume_ranges = {
    "NIFTY 50": (300000000, 400000000),  # 30-40 crore shares
    "SBILIFE": (9000000, 12000000),       # 90 lakhs - 1.2 crore
    "TECHM": (7000000, 9000000),         # 70-90 lakh shares
    "TCS": (3000000, 4000000),           # 30-40 lakh shares
    "INFY": (4000000, 5000000),          # 40-50 lakh shares
    "ULTRACEMCO": (600000, 800000),      # 6-8 lakh shares
    "HINDUNILVR": (1000000, 1500000),    # 10-15 lakh shares
    "GRASIM": (800000, 1000000),         # 8-10 lakh shares
    "INDUSINDBK": (2500000, 3000000),    # 25-30 lakh shares
    "ICICIBANK": (5000000, 6000000),     # 50-60 lakh shares
    "RELIANCE": (4000000, 5000000),      # 40-50 lakh shares
    "HDFCBANK": (3500000, 4500000),      # 35-45 lakh shares
    "ITC": (7000000, 8000000),           # 70-80 lakh shares
    "HCLTECH": (1800000, 2200000),       # 18-22 lakh shares
    "TITAN": (900000, 1100000),          # 9-11 lakh shares
    "HDFCLIFE": (2200000, 2600000),      # 22-26 lakh shares
    "WIPRO": (3400000, 3800000),         # 34-38 lakh shares
    "NESTLEIND": (100000, 150000),       # 1-1.5 lakh shares
    "LT": (1200000, 1500000),            # 12-15 lakh shares
    "TATACONSUM": (1500000, 1800000),    # 15-18 lakh shares
    "KOTAKBANK": (1900000, 2200000),     # 19-22 lakh shares
    "SUNPHARMA": (1400000, 1700000),     # 14-17 lakh shares
    "M&M": (1100000, 1400000),           # 11-14 lakh shares
    "HINDALCO": (3200000, 3600000),      # 32-36 lakh shares
    "ONGC": (5700000, 6300000),          # 57-63 lakh shares
    "ASIANPAINT": (800000, 1000000),     # 8-10 lakh shares
    "EICHERMOT": (450000, 500000),       # 4.5-5 lakh shares
    "BHARTIARTL": (2500000, 2800000),    # 25-28 lakh shares
    "CIPLA": (1300000, 1500000),         # 13-15 lakh shares
    "COALINDIA": (4100000, 4500000),     # 41-45 lakh shares
    "SBIN": (4600000, 5000000),          # 46-50 lakh shares
    "HEROMOTOCO": (340000, 380000),      # 3.4-3.8 lakh shares
    "MARUTI": (230000, 260000),          # 2.3-2.6 lakh shares
    "TATASTEEL": (8700000, 9200000),     # 87-92 lakh shares
    "TATAMOTORS": (2800000, 3200000),    # 28-32 lakh shares
    "NTPC": (5200000, 5600000),          # 52-56 lakh shares
    "JSWSTEEL": (1800000, 2100000),      # 18-21 lakh shares
    "BAJAJ-AUTO": (200000, 250000),      # 2-2.5 lakh shares
    "BAJFINANCE": (650000, 700000),      # 6.5-7 lakh shares
    "DRREDDY": (300000, 350000),         # 3-3.5 lakh shares
    "JIOFIN": (6700000, 7100000),        # 67-71 lakh shares
    "BEL": (5400000, 5800000),           # 54-58 lakh shares
    "BAJAJFINSV": (870000, 950000),      # 8.7-9.5 lakh shares
    "POWERGRID": (4300000, 4700000),     # 43-47 lakh shares
    "APOLLOHOSP": (400000, 450000),      # 4-4.5 lakh shares
    "AXISBANK": (3200000, 3600000),      # 32-36 lakh shares
    "ETERNAL": (1800000, 2100000),       # 18-21 lakh shares
    "TRENT": (800000, 900000),           # 8-9 lakh shares
    "ADANIPORTS": (1700000, 1900000),    # 17-19 lakh shares
    "ADANIENT": (1500000, 1700000),      # 15-17 lakh shares
    "SHRIRAMFIN": (1200000, 1400000)     # 12-14 lakh shares
}

# 52 Week High/Low percentage ranges
# Format: (low_pct, high_pct) - percentage of current price
fifty_two_week_ranges = {
    company: (0.8, 1.1) for company in nifty_companies  # Default: 80% - 110% of current price
}

def format_currency(value):
    """Format number with commas for Indian currency format"""
    if isinstance(value, str):
        return value
    
    # Convert to string with 2 decimal places
    s = f"{value:.2f}"
    
    # Split integer and decimal parts
    parts = s.split('.')
    integer_part = parts[0]
    
    # Add commas for Indian number system (lakhs, crores)
    result = ""
    if len(integer_part) > 3:
        result = "," + integer_part[-3:]
        integer_part = integer_part[:-3]
        
        # Process remaining digits in groups of 2
        i = len(integer_part)
        while i > 0:
            if i >= 2:
                result = "," + integer_part[i-2:i] + result
                i -= 2
            else:
                result = integer_part[0:i] + result
                break
    else:
        result = integer_part
    
    # Add decimal part if it exists
    if len(parts) > 1:
        return result + "." + parts[1]
    return result

def generate_company_data(company_name, base_date):
    """Generate data for a single company for a single day"""
    base_price = random.uniform(price_ranges[company_name][0], price_ranges[company_name][1])
    
    # Calculate fluctuation percentages for high and low
    high_fluctuation = random.uniform(0.5, 3.0) / 100  # 0.5% to 3% fluctuation for high
    low_fluctuation = random.uniform(0.5, 3.0) / 100   # 0.5% to 3% fluctuation for low
    
    # Set open price with slight variation from base price
    open_price = base_price * (1 + random.uniform(-0.5, 0.5) / 100)
    high_price = base_price * (1 + high_fluctuation)
    low_price = base_price * (1 - low_fluctuation)
    
    # Ensure low price is less than open price and high price is higher than open price
    if low_price > open_price:
        low_price = open_price * (1 - random.uniform(0.1, 0.5) / 100)
    if high_price < open_price:
        high_price = open_price * (1 + random.uniform(0.1, 0.5) / 100)
    
    # Previous close should be slightly different from open
    prev_close = open_price * (1 + random.uniform(-1.0, 1.0) / 100)
    
    # Last traded price (LTP) between low and high
    ltp = random.uniform(low_price, high_price)
    
    # Calculate change and percent change
    change = ltp - prev_close
    percent_change = (change / prev_close) * 100
    
    # Generate volume
    volume = random.randint(volume_ranges[company_name][0], volume_ranges[company_name][1])
    
    # Calculate value (in crores) based on average price and volume
    avg_price = (open_price + high_price + low_price + ltp) / 4
    value_in_crores = (avg_price * volume) / 10000000  # Convert to crores
    
    # Generate 52-week high and low
    fifty_two_week_low = base_price * fifty_two_week_ranges[company_name][0]
    fifty_two_week_high = base_price * fifty_two_week_ranges[company_name][1]
    
    # Generate 30-day percent change
    thirty_day_percent_change = random.uniform(-5.0, 10.0)
    
    # Special case for NIFTY 50 index - round to 2 decimal places
    if company_name == "NIFTY 50":
        open_price = round(open_price, 2)
        high_price = round(high_price, 2)
        low_price = round(low_price, 2)
        prev_close = round(prev_close, 2)
        ltp = round(ltp, 2)
        change = round(change, 2)
        fifty_two_week_low = round(fifty_two_week_low, 2)
        fifty_two_week_high = round(fifty_two_week_high, 2)
    
    # Create the company data dictionary
    company_data = {
        "Open": format_currency(open_price),
        "High": format_currency(high_price),
        "Low": format_currency(low_price),
        "PREV. CLOSE": format_currency(prev_close),
        "LTP": format_currency(ltp),
        "Indicative Close": "-",
        "Change": format_currency(change),
        "% Change": f"{percent_change:.2f}",
        "Volume (shares)": f"{volume:,}".replace(',', ','),
        "Value (₹ Crores)": f"{value_in_crores:.2f}",
        "52W High": format_currency(fifty_two_week_high),
        "52W Low": format_currency(fifty_two_week_low),
        "30 d % Change": f"{thirty_day_percent_change:.2f}"
    }
    
    return company_data

def generate_daily_data(date):
    """Generate data for all companies for a given date"""
    companies_data = {}
    
    for company in nifty_companies:
        companies_data[company] = generate_company_data(company, date)
    
    # Create the complete data entry with timestamp and object ID
    timestamp = date.strftime("%Y-%m-%d %H:%M:%S")
    
    # Generate a MongoDB-like ObjectId
    object_id = str(uuid4()).replace("-", "")[:24]
    
    data_entry = {
        "_id": {
            "$oid": object_id
        },
        "timestamp": timestamp,
        "companies": companies_data
    }
    
    return data_entry

def generate_and_save_market_data(days=40):
    """Generate market data for specified number of days and save each day as a separate JSON file"""
    end_date = datetime.datetime(2025, 1, 28)  # End with given date
    start_date = end_date - timedelta(days=days-1)  # Calculate start date
    
    # Create directory for output files if it doesn't exist
    output_dir = "NIFTY50_Data"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Keep track of all generated files
    generated_files = []
    current_date = start_date
    
    while current_date <= end_date:
        # Skip weekends (Saturday and Sunday)
        if current_date.weekday() < 5:  # 0-4 are Monday to Friday
            # Generate a random trading hour between 9:00 AM and 3:30 PM
            hour = random.randint(9, 15)
            minute = random.randint(0, 59)
            if hour == 15:  # If hour is 3 PM, ensure minute is <= 30
                minute = random.randint(0, 30)
                
            trading_datetime = current_date.replace(hour=hour, minute=minute, second=random.randint(0, 59))
            daily_data = generate_daily_data(trading_datetime)
            
            # Format date for filename
            date_str = trading_datetime.strftime("%Y-%m-%d")
            filename = f"NIFTY50_{date_str}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Save individual day data to its own JSON file
            with open(filepath, "w") as file:
                json.dump({"data": [daily_data]}, file, indent=2)
            
            generated_files.append(filepath)
            print(f"Generated data for {date_str} saved to {filepath}")
        
        current_date += timedelta(days=1)
    
    # Create an index file that lists all generated files
    index_filepath = os.path.join(output_dir, "index.json")
    with open(index_filepath, "w") as file:
        json.dump({
            "files": generated_files,
            "count": len(generated_files),
            "date_range": {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d")
            }
        }, file, indent=2)
    
    print(f"\nGeneration complete. Created {len(generated_files)} files.")
    print(f"Index file created at {index_filepath}")
    
    return generated_files

# Generate approximately 1 month (21-22 trading days) of market data
# Each day's data will be saved to a separate file
generated_files = generate_and_save_market_data(days=31)  # 31 calendar days ≈ 22 trading days