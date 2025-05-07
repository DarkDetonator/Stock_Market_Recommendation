from pymongo import MongoClient
import pandas as pd
import numpy as np
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import schedule
import time
from datetime import datetime, timedelta
import os

# Connect to MongoDB
client = MongoClient("mongodb://localhost:27017")
db = client["Money_control"]
collection = db["myNewCollection1"]
predictions_collection = db["weekly_predictions"]

# List of relevant companies
companies_list = ["SBILIFE", "TECHM", "TCS", "INFY", "ULTRACEMCO", "HINDUNILVR", "GRASIM", "INDUSINDBK", "ICICIBANK",
                  "RELIANCE", "HDFCBANK", "ITC", "HCLTECH", "TITAN", "HDFCLIFE", "WIPRO", "NESTLEIND", "LT",
                  "TATACONSUM", "KOTAKBANK", "SUNPHARMA", "M&M", "HINDALCO", "ONGC", "ASIANPAINT", "EICHERMOT",
                  "BHARTIARTL", "CIPLA", "COALINDIA", "SBIN", "HEROMOTOCO", "MARUTI", "TATASTEEL", "TATAMOTORS",
                  "NTPC", "JSWSTEEL", "BAJAJ-AUTO", "BAJFINANCE", "DRREDDY", "JIOFIN", "BEL", "BAJAJFINSV",
                  "POWERGRID", "APOLLOHOSP", "AXISBANK", "ETERNAL", "TRENT", "ADANIPORTS", "ADANIENT", "SHRIRAMFIN"]

# Function to convert string values to float
def clean_value(value):
    if isinstance(value, str):
        return float(value.replace('₹', '').replace(',', '').strip())
    return value

# Function to fetch and preprocess data with a sliding window
def fetch_and_preprocess_data(prediction_horizon_days):
    cursor = collection.find()
    records = list(cursor)
    print(f"Found {len(records)} records in MongoDB")

    data = []
    for record in records:
        if "data" in record and isinstance(record["data"], list) and len(record["data"]) > 0:
            timestamp = record["data"][0].get("timestamp")
            companies = record["data"][0].get("companies", {})
        else:
            companies = record.get("companies", {})
            timestamp = record.get("timestamp")

        for company_key, company_data in companies.items():
            if "NIFTY" in company_key:
                continue
            if company_key in companies_list and isinstance(company_data, dict):
                entry = {"company": company_key, "timestamp": timestamp}
                for key, value in company_data.items():
                    try:
                        entry[key] = clean_value(value)
                    except (ValueError, TypeError):
                        entry[key] = value
                data.append(entry)

    df = pd.DataFrame(data)
    print(f"Created DataFrame with {len(df)} rows and {len(df.columns)} columns")
    print(f"Columns: {df.columns.tolist()}")

    if "Open" not in df.columns or "LTP" not in df.columns:
        print("ERROR: Could not find suitable Open and LTP columns")
        return None

    # Convert timestamp to datetime for sorting
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Use the last 60 days of data as a sliding window (adjust based on data availability)
    end_date = df["timestamp"].max()
    start_date = end_date - timedelta(days=60)
    df_filtered = df[(df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)].copy()

    df_filtered = df_filtered.dropna(subset=["Open", "LTP"])
    df_filtered["Open"] = pd.to_numeric(df_filtered["Open"], errors="coerce")
    df_filtered["LTP"] = pd.to_numeric(df_filtered["LTP"], errors="coerce")
    df_filtered = df_filtered.dropna(subset=["Open", "LTP"])

    df_filtered["growth_score"] = (df_filtered["LTP"] - df_filtered["Open"]) / df_filtered["Open"]
    min_score = df_filtered["growth_score"].min()
    max_score = df_filtered["growth_score"].max()
    range_score = max_score - min_score
    if range_score == 0:
        df_filtered["growth_score_norm"] = 0.5
    else:
        df_filtered["growth_score_norm"] = (df_filtered["growth_score"] - min_score) / range_score

    column_mapping = {
        "Open": ["Open", "OPEN", "open"],
        "High": ["High", "HIGH", "high"],
        "Low": ["Low", "LOW", "low"],
        "52W High": ["52W High", "52w high", "52_week_high", "52W_H"],
        "52W Low": ["52W Low", "52w low", "52_week_low", "52W_L"],
        "Volume": ["Volume", "VOLUME", "volume", "Volume (shares)"]
    }

    available_features = []
    for standard_name, variations in column_mapping.items():
        found_col = next((col for col in variations if col in df_filtered.columns), None)
        if found_col:
            if found_col != standard_name:
                df_filtered[standard_name] = df_filtered[found_col]
            available_features.append(standard_name)

    if "Change" in df_filtered.columns:
        available_features.append("Change")
    if "% Change" in df_filtered.columns:
        available_features.append("% Change")

    if len(available_features) < 2:
        print(f"WARNING: Not enough features found. Using numeric columns.")
        numeric_cols = df_filtered.select_dtypes(include=['number']).columns.tolist()
        exclude_cols = ['growth_score', 'growth_score_norm', 'timestamp', 'LTP']
        available_features = [col for col in numeric_cols if col not in exclude_cols and col != 'company']

    print(f"Using features: {available_features}")

    df_ml = df_filtered.dropna(subset=available_features)
    print(f"Final dataset for ML: {len(df_ml)} rows")

    if len(df_ml) < 10:
        print("ERROR: Not enough data points to train a model")
        return None

    return df_ml, available_features

# Function to train model and make predictions
def train_and_predict(df_ml, available_features, prediction_horizon_days):
    X = df_ml[available_features]
    y = df_ml["growth_score_norm"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(learning_rate=0.1, max_depth=3, n_estimators=100, subsample=1.0, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    print(f"✅ Model trained! Test set MSE: {mse:.6f}")

    # Extrapolate prediction for the chosen horizon (simple linear extrapolation based on recent trend)
    recent_trend = y_train.mean()  # Use mean growth score as a basic trend indicator
    horizon_factor = prediction_horizon_days / 7  # Normalize to weeks (1 week = 7 days)
    df_ml["predicted_growth_score"] = model.predict(X) + (recent_trend * horizon_factor)
    # Clip values to [0, 1] to keep them normalized
    df_ml["predicted_growth_score"] = df_ml["predicted_growth_score"].clip(0, 1)

    return df_ml

# Function to store predictions
def store_predictions(df_ml, week_date):
    predictions = df_ml[["company", "timestamp", "predicted_growth_score"]]
    predictions_dict = predictions.to_dict("records")
    predictions_collection.insert_many([{"week_date": week_date, **pred} for pred in predictions_dict])
    print(f"Stored predictions for week starting {week_date} in MongoDB")

# Function to compare with previous predictions
def compare_with_previous_predictions(current_df, current_week):
    previous_week = (datetime.strptime(current_week, "%Y%m%d") - timedelta(days=7)).strftime("%Y%m%d")
    previous_predictions = list(predictions_collection.find({"week_date": previous_week}))

    if not previous_predictions:
        print(f"No previous predictions found for week {previous_week}")
        current_df["previous_predicted_growth_score"] = np.nan
        current_df["prediction_change"] = 0.0
        current_df["recommendation_score"] = current_df["predicted_growth_score"]
        return current_df

    previous_df = pd.DataFrame(previous_predictions)
    previous_df = previous_df.rename(columns={"predicted_growth_score": "previous_predicted_growth_score"})

    merged_df = current_df.merge(
        previous_df[["company", "timestamp", "previous_predicted_growth_score"]],
        on=["company", "timestamp"],
        how="left"
    )

    merged_df["prediction_change"] = merged_df["predicted_growth_score"] - merged_df["previous_predicted_growth_score"].fillna(0)
    merged_df["recommendation_score"] = merged_df["predicted_growth_score"] + merged_df["prediction_change"].fillna(0)
    return merged_df

# Function to generate recommendations
def generate_recommendations(df_with_comparison):
    top_stocks = df_with_comparison.groupby('company')['recommendation_score'].mean().sort_values(ascending=False)
    print("\nTop 10 Recommended Stocks (based on predicted growth and trend):")
    print(top_stocks.head(10))

    bottom_stocks = df_with_comparison.groupby('company')['recommendation_score'].mean().sort_values()
    print("\nBottom 10 Stocks to Avoid:")
    print(bottom_stocks.head(10))

    df_with_comparison[["company", "timestamp", "predicted_growth_score", "prediction_change", "recommendation_score"]].to_csv(
        f"stock_recommendations_{datetime.now().strftime('%Y%m%d')}.csv", index=False
    )
    print(f"\nRecommendations saved to 'stock_recommendations_{datetime.now().strftime('%Y%m%d')}.csv'")

# Function to get user input and provide company-specific score
def get_company_score(df_with_comparison):
    while True:
        company_name = input("\nEnter a company name (e.g., TCS) to get its predicted score and comparison, or 'exit' to quit: ").upper()
        if company_name == 'EXIT':
            break
        
        if company_name not in companies_list:
            print(f"Company {company_name} not found in the list. Available companies: {companies_list[:5]}... (total {len(companies_list)})")
            continue

        company_data = df_with_comparison[df_with_comparison['company'] == company_name]
        if company_data.empty:
            print(f"No data available for {company_name} this week.")
            continue

        current_score = company_data["predicted_growth_score"].mean()
        previous_score = company_data["previous_predicted_growth_score"].mean()
        change = company_data["prediction_change"].mean()

        print(f"\nScore for {company_name}:")
        print(f"Current Predicted Growth Score: {current_score:.6f}")
        if pd.notna(previous_score):
            print(f"Previous Week's Predicted Growth Score: {previous_score:.6f}")
            print(f"Change from Last Week: {change:.6f}")
        else:
            print("No previous prediction available for comparison.")
        
        print(f"Recommendation Score (including trend): {company_data['recommendation_score'].mean():.6f}")

# Function to get prediction horizon from user
def get_prediction_horizon():
    while True:
        print("\nSelect prediction horizon:")
        print("1. 1 Week")
        print("2. 1 Month")
        print("3. 3 Months")
        print("4. 6 Months")
        choice = input("Enter choice (1-4): ")
        horizon_map = {
            "1": 7,    # 1 week = 7 days
            "2": 30,   # 1 month = ~30 days
            "3": 90,   # 3 months = ~90 days
            "4": 180   # 6 months = ~180 days
        }
        if choice in horizon_map:
            return horizon_map[choice]
        print("Invalid choice. Please enter 1, 2, 3, or 4.")

# Main function to run weekly predictions
def run_weekly_predictions():
    current_week = datetime.now().strftime("%Y%m%d")
    print(f"\nRunning predictions for week starting {current_week}")

    # Get prediction horizon from user
    prediction_horizon_days = get_prediction_horizon()
    print(f"Selected prediction horizon: {prediction_horizon_days} days")

    result = fetch_and_preprocess_data(prediction_horizon_days)
    if result is None:
        return
    df_ml, available_features = result

    df_ml = train_and_predict(df_ml, available_features, prediction_horizon_days)
    store_predictions(df_ml, current_week)
    df_with_comparison = compare_with_previous_predictions(df_ml, current_week)
    generate_recommendations(df_with_comparison)
    get_company_score(df_with_comparison)

# Schedule weekly predictions (e.g., every Monday at 9 AM)
schedule.every().monday.at("09:00").do(run_weekly_predictions)

# Run immediately for testing
run_weekly_predictions()

# Keep the script running to execute scheduled tasks
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute