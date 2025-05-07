import pandas as pd
import numpy as np
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ServerSelectionTimeoutError
import logging
import time
from datetime import datetime, timedelta
from xgboost import XGBRegressor
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import mean_squared_error
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StockPredictor:
    def __init__(self, mongo_uri="mongodb://localhost:27017/", db_name="Money_control", collection_name="myNewCollection1", nifty_companies=None, company_name_to_ticker=None):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.data_collection = None
        self.predictions_collection = None
        self._prediction_cache = {}
        self._last_data_update = None
        self.nifty50 = nifty_companies or []
        self.company_name_to_ticker = company_name_to_ticker or {}
        
        self.sector_mapping = {
            'TCS': 'IT', 'INFY': 'IT', 'HCLTECH': 'IT', 'WIPRO': 'IT', 'TECHM': 'IT',
            'HDFCBANK': 'Banking', 'ICICIBANK': 'Banking', 'SBIN': 'Banking', 'KOTAKBANK': 'Banking', 'AXISBANK': 'Banking', 'INDUSINDBK': 'Banking',
            'RELIANCE': 'Conglomerate', 'HINDUNILVR': 'FMCG', 'ITC': 'FMCG', 'NESTLEIND': 'FMCG', 'TATACONSUM': 'FMCG',
            'MARUTI': 'Automobile', 'M&M': 'Automobile', 'TATAMOTORS': 'Automobile', 'HEROMOTOCO': 'Automobile', 'BAJAJ-AUTO': 'Automobile', 'EICHERMOT': 'Automobile',
            'SUNPHARMA': 'Pharma', 'DRREDDY': 'Pharma', 'CIPLA': 'Pharma',
            'LT': 'Construction', 'ULTRACEMCO': 'Cement', 'GRASIM': 'Cement',
            'BHARTIARTL': 'Telecom', 'TATASTEEL': 'Metals', 'JSWSTEEL': 'Metals', 'HINDALCO': 'Metals',
            'ONGC': 'Oil & Gas', 'COALINDIA': 'Mining', 'NTPC': 'Power', 'POWERGRID': 'Power',
            'BAJFINANCE': 'Finance', 'BAJAJFINSV': 'Finance', 'HDFCLIFE': 'Insurance', 'SBILIFE': 'Insurance', 'JIOFIN': 'Finance',
            'ASIANPAINT': 'Paints', 'TITAN': 'Consumer Durables', 'APOLLOHOSP': 'Healthcare',
            'ADANIPORTS': 'Infrastructure', 'ADANIENT': 'Conglomerate', 'TRENT': 'Retail', 'SHRIRAMFIN': 'Finance', 'BEL': 'Defense'
        }
        
        self._connect_to_mongo(max_retries=3, delay=2)
        
        if self.client:
            self.predictions_collection.create_index([("week_date", ASCENDING), ("company", ASCENDING)])
            self.data_collection.create_index([("data.timestamp", ASCENDING)])

    def _connect_to_mongo(self, max_retries=3, delay=2):
        attempt = 0
        while attempt < max_retries:
            try:
                self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
                self.db = self.client[self.db_name]
                self.data_collection = self.db[self.collection_name]
                self.predictions_collection = self.db["weekly_predictions"]
                self.client.server_info()
                logger.info("Successfully connected to MongoDB")
                return
            except ServerSelectionTimeoutError as e:
                attempt += 1
                logger.error(f"Connection attempt {attempt} failed: {str(e)}")
                if attempt == max_retries:
                    logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                    return
                time.sleep(delay)

    def clean_numeric_value(self, value):
        if value is None or value == "-":
            return 0.0
        try:
            cleaned_value = str(value).replace('₹', '').replace(',', '').replace('%', '').strip()
            return float(cleaned_value) if cleaned_value else 0.0
        except (ValueError, TypeError) as e:
            logger.warning(f"Failed to clean numeric value: {value} ({str(e)})")
            return 0.0

    def _fetch_historical_data(self, company, days=60):
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            ticker = self.company_name_to_ticker.get(company, company)
            logger.debug(f"Fetching historical data for {company} (ticker: {ticker}) from {start_date} to {end_date}")
            
            records = self.data_collection.find({
                "data.timestamp": {"$gte": start_date.strftime("%Y-%m-%d %H:%M:%S")}
            })
            
            data = []
            for record in records:
                for entry in record.get("data", []):
                    timestamp = entry.get("timestamp")
                    companies = entry.get("companies", {})
                    if ticker in companies and isinstance(companies[ticker], dict):
                        entry_data = {"timestamp": pd.to_datetime(timestamp)}
                        numeric_fields = ["Open", "High", "Low", "PREV. CLOSE", "LTP", "Change", "% Change",
                                       "Volume (shares)", "Value (₹ Crores)", "52W High", "52W Low", "30 d % Change",
                                       "PE Ratio", "PB Ratio", "EV/EBITDA", "Market Cap", "Revenue"]
                        for key in numeric_fields:
                            value = companies[ticker].get(key)
                            entry_data[key] = self.clean_numeric_value(value)
                        data.append(entry_data)
            
            logger.info(f"Fetched {len(data)} records for {company} from {start_date} to {end_date}")
            if not data:
                logger.warning(f"No historical data found for {company} (ticker: {ticker})")
                return None
            
            df = pd.DataFrame(data)
            if df.empty:
                logger.warning(f"Empty DataFrame after processing for {company} (ticker: {ticker})")
                return None
                
            df = df.sort_values("timestamp")
            df = df.set_index("timestamp")
            numeric_cols = [col for col in df.columns if df[col].dtype in [np.float64, np.int64]]
            if not numeric_cols:
                logger.warning(f"No numeric columns available for {company} (ticker: {ticker})")
                return None
            df = df[numeric_cols].resample("D").mean().fillna(method="ffill").tail(60)
            logger.info(f"Processed {len(df)} days of historical data for {company} with columns: {df.columns.tolist()}")
            return df
        except Exception as e:
            logger.error(f"Error fetching historical data for {company}: {str(e)}")
            return None

    def _calculate_metrics(self, df, company, current_price):
        price_trend = df["% Change"].mean() if "% Change" in df else (current_price - df["LTP"].iloc[0]) / df["LTP"].iloc[0] if len(df) > 1 and "LTP" in df else 0
        price_trend = 0 if np.isnan(price_trend) else price_trend

        thirty_day_trend = df["30 d % Change"].iloc[-1] / 100 if "30 d % Change" in df else 0
        thirty_day_trend = 0 if np.isnan(thirty_day_trend) else thirty_day_trend

        if "Revenue" in df and not df["Revenue"].isna().all() and (df["Revenue"] != 0).any():
            revenue_changes = df["Revenue"].pct_change()
            revenue_trend = revenue_changes.mean() if not revenue_changes.isna().all() else 0
        else:
            revenue_trend = 0
        revenue_trend = 0 if np.isnan(revenue_trend) else revenue_trend

        pe_ratio = df.get("PE Ratio", pd.Series([20])).iloc[-1] if "PE Ratio" in df else 20
        pe_ratio = 20 if np.isnan(pe_ratio) else pe_ratio
        pb_ratio = df.get("PB Ratio", pd.Series([3])).iloc[-1] if "PB Ratio" in df else 3
        pb_ratio = 3 if np.isnan(pb_ratio) else pb_ratio
        ev_ebitda = df.get("EV/EBITDA", pd.Series([10])).iloc[-1] if "EV/EBITDA" in df else 10
        ev_ebitda = 10 if np.isnan(ev_ebitda) else ev_ebitda
        
        company_sector = self.sector_mapping.get(company, "Unknown")
        sector_peers = [c for c, s in self.sector_mapping.items() if s == company_sector and c != company]
        sector_similarity = len(sector_peers) / len(self.nifty50) if sector_peers else 0
        
        news_collection = self.db["NEWS_DATA"]
        news = news_collection.find({"companies": company})
        sentiment_score = 0
        news_count = 0
        for item in news:
            for category in ["business", "markets", "stocks", "companies", "trends", "ipo"]:
                for news_item in item.get(category, []):
                    sentiment = news_item.get("sentiment", 0)
                    sentiment_score += sentiment
                    news_count += 1
        sentiment_trend = sentiment_score / news_count if news_count > 0 else 0
        sentiment_trend = 0 if np.isnan(sentiment_trend) else sentiment_trend
        
        market_cap = df.get("Market Cap", pd.Series([100000])).iloc[-1] if "Market Cap" in df else 100000
        market_cap = 100000 if np.isnan(market_cap) else market_cap
        if market_cap > 200000:
            market_cap_tier = "Large-cap"
        elif market_cap > 50000:
            market_cap_tier = "Mid-cap"
        else:
            market_cap_tier = "Small-cap"
        
        returns = df["% Change"] / 100 if "% Change" in df else df["LTP"].pct_change().dropna() if "LTP" in df else pd.Series([])
        volatility = returns.std() * np.sqrt(252) if len(returns) > 1 else 0.3
        volatility = 0.3 if np.isnan(volatility) else volatility

        nifty_data = self._fetch_historical_data("NIFTY 50", days=60)
        if nifty_data is not None and "% Change" in nifty_data:
            nifty_returns = nifty_data["% Change"] / 100
            if len(returns) == len(nifty_returns):
                beta = returns.corr(nifty_returns) * returns.std() / nifty_returns.std() if nifty_returns.std() != 0 else 1
            else:
                beta = 1
        else:
            beta = 1
        beta = 1 if np.isnan(beta) else beta
        
        return {
            "price_trend": price_trend,
            "thirty_day_trend": thirty_day_trend,
            "revenue_trend": revenue_trend,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "ev_ebitda": ev_ebitda,
            "sector_similarity": sector_similarity,
            "sentiment_trend": sentiment_trend,
            "market_cap_tier": market_cap_tier,
            "volatility": volatility,
            "beta": beta,
            "volume": df.get("Volume (shares)", pd.Series([1000000])).iloc[-1],
            "week_high": df.get("52W High", pd.Series([current_price * 1.1])).iloc[-1],
            "week_low": df.get("52W Low", pd.Series([current_price * 0.9])).iloc[-1],
            "recent_percent_change": df["% Change"].iloc[-1] if "% Change" in df else (current_price - df["LTP"].iloc[-1]) / df["LTP"].iloc[-1] if "LTP" in df else 0
        }

    def _prepare_features(self, df):
        if "LTP" not in df:
            logger.warning("LTP column missing in DataFrame")
            return None, None
        df["lag_1"] = df["LTP"].shift(1)
        df["lag_5"] = df["LTP"].shift(5)
        df["ma_5"] = df["LTP"].rolling(window=5).mean()
        df["ma_20"] = df["LTP"].rolling(window=20).mean()
        df["returns"] = df["% Change"] / 100 if "% Change" in df else df["LTP"].pct_change()
        df["volatility"] = df["returns"].rolling(window=20).std() * np.sqrt(252)
        df["volume_ma_5"] = df.get("Volume (shares)", pd.Series([1000000])).rolling(window=5).mean()
        df["range_52w"] = (df.get("52W High", df["LTP"] * 1.1) - df.get("52W Low", df["LTP"] * 0.9)) / df["LTP"]
        df["thirty_day_trend"] = df.get("30 d % Change", pd.Series([0])) / 100
        df["recent_change"] = df["% Change"] / 100 if "% Change" in df else df["LTP"].pct_change()
        df["trend_direction"] = df["returns"].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        df = df.dropna()
        features = ["lag_1", "lag_5", "ma_5", "ma_20", "volatility", "volume_ma_5", "range_52w", "thirty_day_trend", "recent_change", "trend_direction"]
        return df[features], df["LTP"]

    def get_recommendations(self, horizon=7):
        try:
            current_week = datetime.now().strftime("%Y%m%d")
            logger.info(f"Fetching recommendations for week {current_week} with horizon {horizon}")

            pipeline = [
                {"$match": {"week_date": current_week}},
                {
                    "$project": {
                        "company": 1,
                        "predicted_growth_score": 1,
                        "recommendation_score": 1,
                        "metrics": 1,
                        "weighted_score": {
                            "$add": [
                                {"$multiply": ["$predicted_growth_score", 0.5]},
                                {"$multiply": ["$recommendation_score", 0.3]},
                                {"$multiply": ["$metrics.sentiment_trend", 0.1]},
                                {"$multiply": ["$metrics.price_trend", 0.1]}
                            ]
                        }
                    }
                },
                {"$sort": {"weighted_score": -1}},
                {"$limit": 20}
            ]

            predictions = list(self.predictions_collection.aggregate(pipeline))
            logger.info(f"Found {len(predictions)} predictions for week {current_week}")

            if len(predictions) >= 10:
                top_stocks_df = pd.DataFrame(predictions[:5])
                bottom_stocks_df = pd.DataFrame(predictions[-5:])
                return top_stocks_df, bottom_stocks_df
            else:
                logger.warning(f"Insufficient predictions ({len(predictions)} < 10) for week {current_week}, generating predictions")
                for company in self.nifty50:
                    stock_data = {
                        "company_name": company,
                        "ltp": 100,
                        "percent_change": 0,
                        "volume": 1000000,
                        "week_high": 110,
                        "week_low": 90,
                        "pe_ratio": 20,
                        "pb_ratio": 3,
                        "ev_ebitda": 10,
                        "market_cap": 100000,
                        "30_d_percent_change": 0
                    }
                    try:
                        self.predict(stock_data, horizon)
                    except Exception as e:
                        logger.error(f"Failed to generate prediction for {company}: {str(e)}")

                predictions = list(self.predictions_collection.aggregate(pipeline))
                logger.info(f"After generating, found {len(predictions)} predictions for week {current_week}")

                if len(predictions) > 0:
                    top_stocks_df = pd.DataFrame(predictions[:min(5, len(predictions))])
                    bottom_stocks_df = pd.DataFrame(predictions[-min(5, len(predictions)):])
                    logger.warning(f"Returning partial recommendations with {len(predictions)} predictions")
                    return top_stocks_df, bottom_stocks_df
                else:
                    logger.error(f"No predictions available for week {current_week} after generation attempt")
                    raise ValueError(f"No data available for recommendations after generation attempt")

        except Exception as e:
            logger.error(f"Error in get_recommendations: {str(e)}")
            raise ValueError(f"Error generating recommendations: {str(e)}")

    def predict(self, stock_data, horizon=7):
        cache_key = f"{stock_data['company_name']}_{horizon}"
        if cache_key in self._prediction_cache:
            del self._prediction_cache[cache_key]
        
        if not self.client:
            raise ValueError("MongoDB connection not available for predictions")

        company = stock_data["company_name"]
        current_price = stock_data.get("ltp", 100)
        recent_percent_change = stock_data.get("percent_change", 0) / 100
        if "percent_change" not in stock_data:
            logger.warning(f"percent_change missing for {company}, defaulting to 0")

        historical_data = self._fetch_historical_data(company, days=60)
        if historical_data is None or len(historical_data) < 5:
            logger.warning(f"Insufficient historical data for {company}, using simplified prediction")
            return self._generate_simplified_prediction(stock_data, horizon)
        
        try:
            metrics = self._calculate_metrics(historical_data, company, current_price)
            
            if recent_percent_change == 0:
                fallback_percent_change = metrics["recent_percent_change"] / 100
                if fallback_percent_change != 0:
                    recent_percent_change = fallback_percent_change
                    logger.info(f"Using fallback recent_percent_change {recent_percent_change} for {company}")
                else:
                    logger.warning(f"Both stock_data percent_change and calculated recent_percent_change are 0 for {company}")
            
            X, y = self._prepare_features(historical_data)
            if X is None or len(X) < 5:
                logger.warning(f"Insufficient feature data for {company}, using simplified prediction")
                return self._generate_simplified_prediction(stock_data, horizon)
            
            param_grid = {
                'n_estimators': [50, 100],
                'max_depth': [3, 5],
                'learning_rate': [0.01, 0.1],
                'subsample': [0.8, 1.0]
            }
            xgb = XGBRegressor(random_state=42)
            grid_search = GridSearchCV(xgb, param_grid, cv=3, scoring='neg_mean_squared_error', n_jobs=-1)
            grid_search.fit(X, y)
            best_model = grid_search.best_estimator_
            
            last_features = X.iloc[-1:].copy()
            predictions = []
            for _ in range(horizon):
                pred = best_model.predict(last_features)[0]
                predictions.append(pred)
                last_features["lag_1"] = pred
                last_features["lag_5"] = last_features["lag_1"].shift(1, fill_value=last_features["lag_1"].iloc[0])
                last_features["ma_5"] = np.mean(predictions[-5:] if len(predictions) >= 5 else predictions + [pred] * (5 - len(predictions)))
                last_features["ma_20"] = last_features["ma_20"].iloc[0]
                last_features["volatility"] = last_features["volatility"].iloc[0]
                last_features["volume_ma_5"] = last_features["volume_ma_5"].iloc[0]
                last_features["range_52w"] = last_features["range_52w"].iloc[0]
                last_features["thirty_day_trend"] = last_features["thirty_day_trend"].iloc[0]
                last_features["recent_change"] = last_features["recent_change"].iloc[0]
                last_features["trend_direction"] = last_features["trend_direction"].iloc[0]
            
            predicted_price = float(predictions[-1])
            predicted_growth = (predicted_price - current_price) / current_price
            
            adjusted_growth = predicted_growth
            if recent_percent_change != 0:
                if recent_percent_change < 0:
                    adjustment_factor = 3.0
                    adjusted_growth = predicted_growth + (recent_percent_change * adjustment_factor)
                    logger.info(f"Applied negative adjustment for {company}: predicted_growth={predicted_growth}, adjusted_growth={adjusted_growth}")
                elif recent_percent_change > 0:
                    adjustment_factor = 0.5
                    adjusted_growth = predicted_growth + (recent_percent_change * adjustment_factor)
                    logger.info(f"Applied positive adjustment for {company}: predicted_growth={predicted_growth}, adjusted_growth={adjusted_growth}")
            
            max_predicted_growth = 0.05
            min_predicted_growth = -0.5
            adjusted_growth = max(min_predicted_growth, min(adjusted_growth, max_predicted_growth))
            predicted_growth_score = max(0, min(1, 0.5 + adjusted_growth * 5))
            
            previous_historical_data = self._fetch_historical_data(company, days=120)
            if previous_historical_data is None or len(previous_historical_data) < 2:
                logger.warning(f"Insufficient previous historical data for {company}, defaulting previous_growth_score")
                previous_growth_score = 0.5
            else:
                previous_price = previous_historical_data["LTP"].iloc[-2] if len(previous_historical_data) > 1 else current_price * 0.99
                previous_end_price = previous_historical_data["LTP"].iloc[-1]
                previous_growth = (previous_end_price - previous_price) / previous_price if previous_price != 0 else 0
                previous_growth_score = max(0, min(1, 0.5 + previous_growth * 5))
            
            prediction_change = predicted_growth_score - previous_growth_score
            recommendation_score = max(0, min(1, (
                predicted_growth_score * 0.5 +
                metrics["price_trend"] * 0.1 +
                metrics["thirty_day_trend"] * 0.1 +
                metrics["sentiment_trend"] * 0.1 +
                (1 - metrics["volatility"]) * 0.05 +
                (1 - metrics["pe_ratio"] / 100) * 0.05 +
                metrics["sector_similarity"] * 0.05 +
                prediction_change * 0.05
            )))
            
            if predicted_growth_score >= 0.8 and recommendation_score < 0.66:
                logger.warning(f"Adjusting recommendation_score for {company} due to high predicted_growth_score ({predicted_growth_score})")
                recommendation_score = max(recommendation_score, 0.66)
            elif predicted_growth_score <= 0.2 and recommendation_score > 0.33:
                logger.warning(f"Adjusting recommendation_score for {company} due to low predicted_growth_score ({predicted_growth_score})")
                recommendation_score = min(recommendation_score, 0.33)
            
            logger.info(f"Prediction for {company}: current_price={current_price}, predicted_price={predicted_price}, "
                       f"predicted_growth={predicted_growth}, adjusted_growth={adjusted_growth}, "
                       f"predicted_growth_score={predicted_growth_score}, previous_growth_score={previous_growth_score}, "
                       f"recent_percent_change={recent_percent_change}, recommendation_score={recommendation_score}")
            
            prediction = {
                "company": company,
                "horizon": horizon,
                "predicted_price": round(predicted_price, 2),
                "predicted_growth_score": round(predicted_growth_score, 3),
                "previous_predicted_growth_score": round(previous_growth_score, 3),
                "prediction_change": round(prediction_change, 3),
                "recommendation_score": round(recommendation_score, 3),
                "horizon_date": (datetime.now() + timedelta(days=horizon)).strftime("%Y-%m-%d"),
                "metrics": {
                    "price_trend": round(metrics["price_trend"], 3),
                    "thirty_day_trend": round(metrics["thirty_day_trend"], 3),
                    "revenue_trend": round(metrics["revenue_trend"], 3),
                    "pe_ratio": round(metrics["pe_ratio"], 2),
                    "pb_ratio": round(metrics["pb_ratio"], 2),
                    "ev_ebitda": round(metrics["ev_ebitda"], 2),
                    "sector_similarity": round(metrics["sector_similarity"], 3),
                    "sentiment_trend": round(metrics["sentiment_trend"], 3),
                    "market_cap_tier": metrics["market_cap_tier"],
                    "volatility": round(metrics["volatility"], 3),
                    "beta": round(metrics["beta"], 3),
                    "volume": round(metrics["volume"], 0),
                    "week_high": round(metrics["week_high"], 2),
                    "week_low": round(metrics["week_low"], 2)
                }
            }
            
            current_week = datetime.now().strftime("%Y%m%d")
            self.predictions_collection.update_one(
                {"week_date": current_week, "company": company},
                {"$set": {
                    "week_date": current_week,
                    "company": company,
                    "predicted_growth_score": predicted_growth_score,
                    "recommendation_score": recommendation_score,
                    "metrics": prediction["metrics"],
                    "timestamp": datetime.now()
                }},
                upsert=True
            )
            
            self._prediction_cache[cache_key] = {
                "timestamp": datetime.now(),
                "data": prediction
            }
            return prediction
            
        except Exception as e:
            logger.error(f"Error in XGBoost prediction for {company}: {str(e)}")
            return self._generate_simplified_prediction(stock_data, horizon)

    def _generate_simplified_prediction(self, stock_data, horizon):
        company = stock_data.get("company_name", "unknown")
        current_price = stock_data.get("ltp", 100)
        recent_change = stock_data.get("percent_change", 0) / 100
        cache_key = f"{company}_{horizon}"  # Define cache_key here
        
        logger.info(f"Generating simplified prediction for {company}: recent_change={recent_change}, current_price={current_price}")
        
        uncertainty_factor = min(1.0, horizon / 30)
        if recent_change < 0:
            adjusted_growth = max(recent_change, -0.5)
            predicted_growth_score = max(0, min(1, 0.5 + adjusted_growth * 5))
        else:
            predicted_growth_score = max(0, min(1, 0.5 + recent_change * 5))
        
        previous_growth_score = max(0, min(1, predicted_growth_score * 0.95))
        
        prediction_change = predicted_growth_score - previous_growth_score
        recommendation_score = max(0, min(1, (
            predicted_growth_score * 0.7 +
            prediction_change * 0.3
        )))
        
        if predicted_growth_score >= 0.8 and recommendation_score < 0.66:
            logger.warning(f"Adjusting simplified recommendation_score for {company} due to high predicted_growth_score ({predicted_growth_score})")
            recommendation_score = max(recommendation_score, 0.66)
        elif predicted_growth_score <= 0.2 and recommendation_score > 0.33:
            logger.warning(f"Adjusting simplified recommendation_score for {company} due to low predicted_growth_score ({predicted_growth_score})")
            recommendation_score = min(recommendation_score, 0.33)
        
        predicted_price = current_price * (1 + (predicted_growth_score - 0.5) * uncertainty_factor)
        
        metrics = {
            "price_trend": recent_change,
            "thirty_day_trend": stock_data.get("30_d_percent_change", 0) / 100,
            "revenue_trend": 0,
            "pe_ratio": stock_data.get("pe_ratio", 20),
            "pb_ratio": stock_data.get("pb_ratio", 3),
            "ev_ebitda": stock_data.get("ev_ebitda", 10),
            "sector_similarity": 0,
            "sentiment_trend": 0,
            "market_cap_tier": stock_data.get("market_cap_tier", "Mid-cap"),
            "volatility": 0.3,
            "beta": 1,
            "volume": stock_data.get("volume", 1000000),
            "week_high": stock_data.get("week_high", current_price * 1.1),
            "week_low": stock_data.get("week_low", current_price * 0.9)
        }
        
        prediction = {
            "company": company,
            "horizon": horizon,
            "predicted_price": round(predicted_price, 2),
            "predicted_growth_score": round(predicted_growth_score, 3),
            "previous_predicted_growth_score": round(previous_growth_score, 3),
            "prediction_change": round(prediction_change, 3),
            "recommendation_score": round(recommendation_score, 3),
            "horizon_date": (datetime.now() + timedelta(days=horizon)).strftime("%Y-%m-%d"),
            "metrics": metrics
        }
        
        current_week = datetime.now().strftime("%Y%m%d")
        self.predictions_collection.update_one(
            {"week_date": current_week, "company": company},
            {"$set": {
                "week_date": current_week,
                "company": company,
                "predicted_growth_score": predicted_growth_score,
                "recommendation_score": recommendation_score,
                "metrics": metrics,
                "timestamp": datetime.now()
            }},
            upsert=True
        )
        
        self._prediction_cache[cache_key] = {
            "timestamp": datetime.now(),
            "data": prediction
        }
        return prediction
