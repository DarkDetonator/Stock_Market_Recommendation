import pandas as pd
from pymongo import MongoClient
import logging
from datetime import datetime, timedelta
from stock_predictor import StockPredictor
from nift50 import Nifty50
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyDataFetcher:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="Money_control", financial_collection="myNewCollection1"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.financial_collection = self.db[financial_collection]
        self.nifty50 = Nifty50()
        self.predictor = StockPredictor(mongo_uri=mongo_uri, db_name=db_name, collection_name=financial_collection, 
                                       nifty_companies=self.nifty50.nifty_companies, 
                                       company_name_to_ticker=self.nifty50.company_name_to_ticker)
        # Temporary storage for news titles
        self.temp_news_titles = []

    def clean_numeric_value(self, value):
        if value is None or value == "-":
            return 0.0
        try:
            cleaned_value = str(value).replace('₹', '').replace(',', '').replace('%', '').strip()
            return float(cleaned_value) if cleaned_value else 0.0
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to clean numeric value: {value} ({str(e)})")
            return 0.0

    def get_company_data(self, symbol):
        try:
            cursor = self.financial_collection.find()
            records = list(cursor)
            logger.info(f"Fetched {len(records)} records for financial data for {symbol}")

            data = []
            for record in records:
                if "data" in record and isinstance(record["data"], list) and len(record["data"]) > 0:
                    for entry in record["data"]:
                        timestamp = entry.get("timestamp")
                        companies = entry.get("companies", {})
                        if symbol in companies and isinstance(companies[symbol], dict):
                            entry_data = {"company": symbol, "timestamp": timestamp}
                            numeric_fields = ["Open", "High", "Low", "PREV. CLOSE", "LTP", "Change", "% Change",
                                             "Volume (shares)", "Value (₹ Crores)", "52W High", "52W Low", "30 d % Change",
                                             "PE Ratio", "PB Ratio", "EV/EBITDA", "Market Cap", "Revenue"]
                            for key, value in companies[symbol].items():
                                if key in numeric_fields:
                                    entry_data[key] = self.clean_numeric_value(value)
                                else:
                                    entry_data[key] = value
                            data.append(entry_data)

            if not data:
                logger.warning(f"No financial data found for {symbol}")
                return {"success": False, "error": f"No data found for {symbol}"}

            df = pd.DataFrame(data)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.sort_values("timestamp")

            latest = df.iloc[-1]
            end_date = df["timestamp"].max()
            start_date = end_date - timedelta(days=2)

            ltp = latest["LTP"]
            if ltp == 0.0:
                ltp = 100.0
                logger.warning(f"Zero LTP for {symbol}, using default: {ltp}")

            prev_close = latest.get("PREV. CLOSE", df.iloc[-2]["LTP"] if len(df) > 1 else ltp * 0.99)
            change = ltp - prev_close
            percent_change = (change / prev_close) * 100 if prev_close != 0 else 0

            # Cap the percent_change to ±3% to avoid extreme changes
            MAX_CHANGE_PERCENT = 3.0
            if percent_change > MAX_CHANGE_PERCENT:
                percent_change = MAX_CHANGE_PERCENT
                change = (percent_change / 100) * prev_close
                ltp = prev_close + change
                logger.info(f"Capped percent_change for {symbol} from {percent_change} to {MAX_CHANGE_PERCENT}%")
            elif percent_change < -MAX_CHANGE_PERCENT:
                percent_change = -MAX_CHANGE_PERCENT
                change = (percent_change / 100) * prev_close
                ltp = prev_close + change
                logger.info(f"Capped percent_change for {symbol} from {percent_change} to {-MAX_CHANGE_PERCENT}%")

            if "Change" in latest and "% Change" in latest:
                logger.info(f"Using provided Change ({change}) and % Change ({percent_change}) for {symbol}")
            else:
                logger.info(f"Calculated Change ({change}) and % Change ({percent_change}) for {symbol}")

            stock_data = {
                "timestamp_str": latest["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "company_name": self.nifty50.get_full_name(symbol) or "Unknown",
                "open_price": float(latest.get("Open", ltp)),
                "high": float(latest.get("High", ltp)),
                "low": float(latest.get("Low", ltp)),
                "prev_close": float(prev_close),
                "ltp": float(ltp),
                "change": float(change),
                "percent_change": float(percent_change),
                "volume": float(latest.get("Volume (shares)", 1000000)),
                "value": float(latest.get("Value (₹ Crores)", (ltp * 1000000) / 10000000)),
                "week_high": float(latest.get("52W High", ltp * 1.1)),
                "week_low": float(latest.get("52W Low", ltp * 0.9)),
                "30_d_percent_change": float(latest.get("30 d % Change", 0)),
                "pe_ratio": float(latest.get("PE Ratio", 20)),
                "pb_ratio": float(latest.get("PB Ratio", 3)),
                "ev_ebitda": float(latest.get("EV/EBITDA", 10)),
                "market_cap": float(latest.get("Market Cap", 100000))
            }

            missing_fields = [field for field in ["Open", "High", "Low", "PREV. CLOSE", "LTP", "Change", "% Change", 
                                                 "Volume (shares)", "52W High", "52W Low", "30 d % Change"]
                             if field not in latest or latest[field] == 0]
            if missing_fields:
                logger.warning(f"Missing or zero values for {symbol}: {missing_fields}")

            company_info = {
                "name": self.nifty50.get_full_name(symbol) or "Unknown",
                "description": (
                    "Tata Consultancy Services Ltd. (TCS) is a global leader in IT services, consulting, and business solutions, headquartered in Mumbai, India. Founded in 1968, TCS is part of the Tata Group and operates in 150 locations across 46 countries, serving clients in industries such as banking, financial services, insurance, retail, and manufacturing. With over 600,000 employees as of 2025, TCS is renowned for its innovative solutions, including digital transformation, cloud services, and AI-driven technologies. The company has consistently been ranked among the top IT service providers globally, achieving a market capitalization of over ₹12.40 lakh crore in 2025."
                    if symbol == "TCS" else
                    "HDFC Life Insurance Company Ltd. is a leading life insurance provider in India, offering a wide range of products including term life, unit-linked insurance plans (ULIPs), endowment policies, and retirement solutions. Established in 2000, the company is a joint venture between HDFC Ltd. and abrdn plc, focusing on financial protection, wealth creation, and customer-centric innovation. HDFC Life is known for its robust digital infrastructure, strong financial performance, and extensive distribution network, serving millions of customers across India." if symbol == "HDFCLIFE" else
                    f"Description for {self.nifty50.get_full_name(symbol) or symbol}. Update this in the database."
                )
            }

            return {"success": True, "stock_data": stock_data, "company_info": company_info}

        except Exception as e:
            logger.error(f"Error fetching financial data for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_company_prediction(self, symbol, horizon=7):
        try:
            stock_data = self.get_company_data(symbol)
            if not stock_data.get("success"):
                logger.warning(f"Cannot generate prediction for {symbol}: {stock_data.get('error')}")
                return {"success": False, "error": stock_data.get('error')}
            
            stock_data["stock_data"]["company_name"] = symbol
            prediction = self.predictor.predict(stock_data["stock_data"], horizon=horizon)
            return {"success": True, "prediction": prediction}
        except Exception as e:
            logger.error(f"Error getting prediction for {symbol}: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_recommendations(self, horizon=7):
        try:
            top_stocks, bottom_stocks = self.predictor.get_recommendations(horizon=horizon)
            return {
                "success": True,
                "top_stocks": top_stocks.to_dict(orient="records"),
                "bottom_stocks": bottom_stocks.to_dict(orient="records")
            }
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return {"success": False, "error": str(e)}

    def _simulate_finbert_sentiment(self, title):
        """
        Simulate FinBERT sentiment analysis by assigning scores based on keywords.
        In a real implementation, this would call a FinBERT model.
        Returns a score between -1 (negative) and +1 (positive).
        """
        title_lower = title.lower()
        positive_keywords = ["rises", "gains", "boost", "surges", "strong", "profit", "winner", "soars"]
        negative_keywords = ["dips", "falls", "decline", "loss", "weak", "demand", "probe", "allegations"]
        
        score = 0.0
        for pos in positive_keywords:
            if pos in title_lower:
                score += 0.3
        for neg in negative_keywords:
            if neg in title_lower:
                score -= 0.3
        # Clip the score to [-1, 1]
        return max(min(score, 1.0), -1.0)

    def search_news_by_company(self, company):
        """
        Search for news articles related to the company from MongoDB.
        - For two-word names (e.g., "Trent Ltd."): Match full name, then main name (without Ltd.), then symbol.
        - For long names (>3 words, e.g., "HDFC Life Insurance Company Ltd."): Match full name, then remove words from the back until first two words remain, then symbol.
        Removes duplicates and calculates sentiment scores for news titles.
        """
        try:
            news_collection = self.db["NEWS_DATA"]
            news = news_collection.find()
            news_data = []
            seen_titles_urls = set()  # To track duplicates based on title and URL
            self.temp_news_titles = []  # Reset temporary storage for news titles

            # Resolve company input to symbol and full name
            symbol = company if company in self.nifty50.nifty_companies else self.nifty50.get_ticker(company)
            if not symbol:
                return {"success": False, "error": f"Invalid company name or symbol: {company}"}

            # Prepare search terms
            company_lower = symbol.lower()  # e.g., "tcs"
            full_name = self.nifty50.get_full_name(symbol).lower()  # e.g., "tata consultancy services ltd."
            words = full_name.split()  # Split into words
            word_count = len(words)

            # List of strings to match, in order of priority
            match_strings = []

            # For two-word names (e.g., "Trent Ltd.")
            if word_count == 2:
                # 1. Full name (e.g., "trent ltd.")
                match_strings.append(full_name)
                # 2. Main name (remove "ltd.")
                main_name = re.sub(r'\bltd\.?\b', '', full_name).strip()  # e.g., "trent"
                match_strings.append(main_name)
                # 3. Symbol (e.g., "trent")
                match_strings.append(company_lower)

            # For long names (>3 words, e.g., "Tata Consultancy Services Ltd.")
            elif word_count > 3:
                # 1. Full name (e.g., "tata consultancy services ltd.")
                match_strings.append(full_name)
                # 2. Iteratively remove words from the back until only first two words remain
                for i in range(word_count - 1, 1, -1):  # Start from full length - 1 down to 2 words
                    partial_name = " ".join(words[:i]).strip()
                    match_strings.append(partial_name)
                # 3. Symbol (e.g., "tcs")
                match_strings.append(company_lower)

            # For other cases (e.g., 3 words like "Tata Motors Ltd."), use the existing logic
            else:
                main_name = re.sub(r'\bltd\.?\b', '', full_name).strip()
                match_strings.append(full_name)
                match_strings.append(main_name)
                match_strings.append(company_lower)

            for item in news:
                categories = ["business", "markets", "stocks", "economy", "companies", "trends", "ipo"]
                for category in categories:
                    if category in item and isinstance(item[category], list):
                        for news_item in item[category]:
                            title = news_item.get("title", "")
                            title_lower = title.lower()
                            description = news_item.get("summary", "").lower()
                            url = news_item.get("link", "")

                            # Check for duplicates using title and URL
                            title_url_key = (title_lower, url)
                            if title_url_key in seen_titles_urls:
                                continue  # Skip duplicates
                            seen_titles_urls.add(title_url_key)

                            # Try matching each string in order
                            matched = False
                            for match_str in match_strings:
                                title_matches = re.search(r'\b' + re.escape(match_str) + r'\b', title_lower)
                                description_matches = description and re.search(r'\b' + re.escape(match_str) + r'\b', description)
                                if title_matches or description_matches:
                                    # Store the title in temporary storage
                                    self.temp_news_titles.append(title)
                                    
                                    # Simulate FinBERT sentiment analysis
                                    sentiment_score = self._simulate_finbert_sentiment(title)
                                    
                                    news_data.append({
                                        "title": title,
                                        "link": url,
                                        "source": news_item.get("source", ""),
                                        "datetime": news_item.get("datetime", ""),
                                        "summary": news_item.get("summary", ""),
                                        "sentiment": sentiment_score
                                    })
                                    matched = True
                                    break  # Stop checking further match strings once we find a match
                            if matched:
                                break  # Stop checking further news items for this record

            if not news_data:
                logger.warning(f"No news found for {company}")
                return {"success": False, "error": f"No news found for {company}"}

            logger.info(f"Fetched {len(news_data)} news items for {company}")
            return {"success": True, "news": news_data}

        except Exception as e:
            logger.error(f"Error searching news for {company}: {str(e)}")
            return {"success": False, "error": str(e)}

    def store_scraped_news(self, company, scraped_news):
        """
        Store scraped news in MongoDB after calculating sentiment scores.
        """
        try:
            news_collection = self.db["NEWS_DATA"]
            # Add sentiment scores to scraped news
            for news_item in scraped_news:
                title = news_item.get("title", "")
                # Store the title in temporary storage
                self.temp_news_titles.append(title)
                # Simulate FinBERT sentiment analysis
                sentiment_score = self._simulate_finbert_sentiment(title)
                news_item["sentiment"] = sentiment_score

            news_collection.update_one(
                {"_id": {"$exists": True}},  # Update any document (or use a specific _id if needed)
                {"$push": {category: {"$each": scraped_news} for category in ["business", "markets", "stocks", "economy", "companies", "trends", "ipo"]}},
                upsert=True
            )
            logger.info(f"Stored {len(scraped_news)} news items for {company}")
        except Exception as e:
            logger.error(f"Error storing news for {company}: {str(e)}")

def format_company_data(data):
    """
    Format the chatbot output with a professional text-based layout without emojis.
    """
    if not data.get("success"):
        return f"**Error**: {data.get('error', 'No data available')}"

    stock_data = data["stock_data"]
    company_info = data["company_info"]
    news_data = data["news"]

    # Financial Data Section
    formatted = (
        f"# Financial Overview: {company_info['name']}\n"
        f"As of: {stock_data['timestamp_str']}\n"
        f"--------------------------------------------------\n"
        f"Open Price: ₹{stock_data['open_price']:.2f}\n"
        f"High: ₹{stock_data['high']:.2f}\n"
        f"Low: ₹{stock_data['low']:.2f}\n"
        f"Previous Close: ₹{stock_data['prev_close']:.2f}\n"
        f"Last Traded Price (LTP): ₹{stock_data['ltp']:.2f}\n"
        f"Change: {stock_data['change']:+.2f} ({stock_data['percent_change']:+.2f}%)\n"
        f"Volume: {stock_data['volume']:,.0f} shares\n"
        f"Value: ₹{stock_data['value']:.2f} Cr\n"
        f"52 Week High: ₹{stock_data['week_high']:.2f}\n"
        f"52 Week Low: ₹{stock_data['week_low']:.2f}\n"
        f"30 Day % Change: {stock_data['30_d_percent_change']:+.2f}%\n"
        f"\n"
    )

    # Company Info Section
    formatted += (
        f"# Company Profile: {company_info['name']}\n"
        f"--------------------------------------------------\n"
        f"{company_info['description']}\n"
        f"\n"
    )

    # News Section
    formatted += (
        f"# Recent News\n"
        f"--------------------------------------------------\n"
        f"{format_news_data(news_data)}"
    )

    return formatted

def format_news_data(news_data):
    """
    Format the news section with clickable hyperlinks and sentiment scores.
    """
    if not news_data.get("success"):
        return f"Error: {news_data.get('error', 'No news available')}\n"
    
    news_list = news_data["news"]
    if not news_list:
        return "No recent news found.\n"
    
    formatted = ""
    for news in news_list[:5]:
        formatted += (
            f"Title: {news['title']}\n"
            f"Source: {news['source']}\n"
            f"Published: {news['datetime']}\n"
            f"Summary: {news['summary']}\n"
            f"Sentiment: {news['sentiment']:+.2f}\n"
            f"Read More: [Link]({news['link']})\n"
            f"--------------------------------------------------\n\n"
        )
    return formatted