from flask import Flask, render_template, request, jsonify, session, redirect
from flask_cors import CORS
import json
from model import CompanyDataFetcher, format_company_data, format_news_data
from nift50 import Nifty50
import plotly
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import numpy as np
import logging
from bson import ObjectId
from functools import wraps

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration
app.secret_key = 'simple-session-key'  # Must match auth_server.py

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

nifty50 = Nifty50()
model = CompanyDataFetcher()
last_data_update = None

# Session Check Decorator
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required. Please log in.'}), 401
        return f(*args, **kwargs)
    return decorated

def extract_company_from_message(message):
    message_lower = message.lower()
    company_name_mapping = {
        "sbi life insurance company ltd": "SBILIFE",
        "sbi life insurance": "SBILIFE",
        "hdfc life insurance": "HDFCLIFE",
        "tata consultancy services": "TCS",
        "reliance industries": "RELIANCE"
    }
    for name, ticker in company_name_mapping.items():
        if name in message_lower:
            return ticker
    for ticker in nifty50.nifty_companies:
        if ticker.lower() in message_lower:
            return ticker
        full_name = nifty50.get_full_name(ticker).lower()
        if full_name in message_lower:
            return ticker
    return None

def sanitize_json(obj):
    if isinstance(obj, dict):
        return {k: sanitize_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json(item) for item in obj]
    elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
        return 0
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, ObjectId):
        return str(obj)
    return obj

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('http://localhost:5001/login')
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.json
        message = data.get('message', '').strip()
        if not message:
            return jsonify({'response': 'Please enter a message'}), 400
        company = extract_company_from_message(message)
        if company:
            financial_data = model.get_company_data(company)
            if not financial_data.get("success"):
                return jsonify({'response': f"No financial data found for {company}: {financial_data.get('error', 'Unknown error')}" }), 200
            news_results = model.search_news_by_company(company)
            if not news_results.get("success"):
                news_summary = f"Error: No news found for {company}"
            else:
                news_items = news_results.get("news", [])
                news_summary = "# Recent News\n"
                news_summary += "--------------------------------------------------\n"
                if not news_items:
                    news_summary += f"No recent news found for {company}\n"
                else:
                    for item in news_items[:3]:
                        news_summary += f"**Title**: {item.get('title', 'N/A')}\n\n"
                        news_summary += f"**Source**: {item.get('source', 'N/A')}\n\n"
                        news_summary += f"**Published**: {item.get('published', 'N/A')}\n\n"
                        news_summary += f"**Summary**: {item.get('summary', 'N/A')}\n\n"
                        sentiment = item.get('sentiment', 0.0)
                        sentiment_label = 'Positive' if sentiment > 0.5 else 'Neutral' if sentiment > 0 else 'Negative'
                        news_summary += f"**Sentiment**: {sentiment:.2f} ({sentiment_label})\n\n"
                        news_summary += f"**Read More**: [Link]({item.get('url', '#')})\n\n"
                    sentiments = [item["sentiment"] for item in news_items if "sentiment" in item]
                    avg_sentiment = round(sum(sentiments) / len(sentiments), 3) if sentiments else 0
                    news_summary += f"**Average Sentiment Score**: {avg_sentiment} (Range: -1 to +1, where positive is bullish)\n"
            stock_data = financial_data.get('stock_data', {})
            stock_response = "# Financial Overview\n"
            stock_response += "--------------------------------------------------\n"
            stock_response += f"**Company**: {company}\n\n"
            stock_response += f"**Last Traded Price (LTP)**: ₹{round(float(stock_data.get('ltp', 0)), 2)}\n\n"
            stock_response += f"**Open Price**: ₹{round(float(stock_data.get('open_price', 0)), 2)}\n\n"
            stock_response += f"**High**: ₹{round(float(stock_data.get('high', 0)), 2)}\n\n"
            stock_response += f"**Low**: ₹{round(float(stock_data.get('low', 0)), 2)}\n\n"
            stock_response += f"**Previous Close**: ₹{round(float(stock_data.get('prev_close', 0)), 2)}\n\n"
            change = round(float(stock_data.get('change', 0)), 2)
            percent_change = round(float(stock_data.get('percent_change', 0)), 2)
            stock_response += f"**Change**: {change} ({percent_change}%)\n\n"
            stock_response += f"**Volume**: {stock_data.get('volume', 'N/A')} shares\n\n"
            stock_response += f"**Value**: ₹{round(float(stock_data.get('value', 0)), 2)} Cr\n\n"
            stock_response += f"**52 Week High**: ₹{round(float(stock_data.get('week_high', 0)), 2)}\n\n"
            stock_response += f"**52 Week Low**: ₹{round(float(stock_data.get('week_low', 0)), 2)}\n\n"
            stock_response += f"**30 Day % Change**: {round(float(stock_data.get('30_d_percent_change', 0)), 2)}%\n"
            response = stock_response + "\n" + news_summary
            return jsonify({'response': response, 'company': company}), 200
        return jsonify({
            'response': "I can provide financial data, news, and predictions for specific companies in the NSE. "
                       "Please mention a company name in your query, for example 'Show me data for TCS' "
                       "or 'Predict for Reliance'."
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/chat: {str(e)}", exc_info=True)
        return jsonify({'response': f"Server error: {str(e)}"}), 500

@app.route('/api/prediction/<company>', methods=['GET'])
@login_required
def get_prediction(company):
    try:
        horizon = request.args.get('horizon', default=7, type=int)
        prediction_data = model.get_company_prediction(company, horizon)
        if not prediction_data.get("success"):
            return jsonify({'error': prediction_data.get('error', 'No prediction data available')}), 404
        prediction = prediction_data["prediction"]
        graph_data = create_prediction_graphs(prediction, company)
        return jsonify({
            'prediction': sanitize_json(prediction),
            'graphs': sanitize_json(graph_data)
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/prediction: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def create_recommendation_graphs(top_stocks, bottom_stocks, all_stocks, theme='dark'):
    try:
        logger.debug(f"Input data - top_stocks: {top_stocks.to_dict()}, bottom_stocks: {bottom_stocks.to_dict()}, all_stocks: {all_stocks.to_dict()}")

        if all_stocks.empty:
            logger.warning("all_stocks is empty, using fallback data")
            all_stocks = pd.DataFrame([
                {"company": c, "recommendation_score": top_stocks[top_stocks["company"] == c]["recommendation_score"].iloc[0] if not top_stocks[top_stocks["company"] == c].empty else 0.5, "category": "Top Recommendations"}
                for c in top_stocks["company"]
            ] + [
                {"company": c, "recommendation_score": bottom_stocks[bottom_stocks["company"] == c]["recommendation_score"].iloc[0] if not bottom_stocks[bottom_stocks["company"] == c].empty else 0.5, "category": "Stocks to Avoid"}
                for c in bottom_stocks["company"]
            ] + [
                {"company": c, "recommendation_score": 0.5, "category": "Other Stocks"}
                for c in nifty50.nifty_companies if c not in top_stocks["company"].values and c not in bottom_stocks["company"].values
            ])

        required_columns = ['company', 'recommendation_score', 'category']
        missing_columns = [col for col in required_columns if col not in all_stocks.columns]
        if missing_columns:
            logger.warning(f"Missing columns in all_stocks: {missing_columns}, adding defaults")
            for col in missing_columns:
                if col == 'category':
                    all_stocks['category'] = 'Other Stocks'
                else:
                    all_stocks[col] = 0.0

        logger.debug("Validating company column")
        if all_stocks['company'].isnull().any():
            logger.warning("Some company names are None, replacing with 'Unknown'")
            all_stocks['company'] = all_stocks['company'].fillna('Unknown')

        logger.debug("Converting recommendation_score to numeric")
        all_stocks['recommendation_score'] = pd.to_numeric(all_stocks['recommendation_score'], errors='coerce').fillna(0.0)
        logger.debug(f"recommendation_score after conversion: {all_stocks['recommendation_score'].tolist()}")

        all_stocks['recommendation_score'] = all_stocks['recommendation_score'].clip(0, 1)
        invalid_scores = all_stocks[all_stocks['recommendation_score'].isnull()]
        if not invalid_scores.empty:
            logger.warning(f"Invalid recommendation scores found: {invalid_scores.to_dict()}")
            all_stocks['recommendation_score'] = all_stocks['recommendation_score'].fillna(0.0)

        logger.debug("Sorting all_stocks by recommendation_score")
        all_stocks = all_stocks.sort_values(by='recommendation_score', ascending=True)
        logger.debug(f"All stocks after sorting: {all_stocks.to_dict()}")

        logger.debug("Defining top and bottom companies")
        top_companies = set(top_stocks['company'].values)
        bottom_companies = set(bottom_stocks['company'].values)
        logger.debug(f"Top companies: {top_companies}, Bottom companies: {bottom_companies}")

        logger.debug("Assigning marker colors and patterns")
        marker_colors = []
        marker_patterns = []
        marker_line_colors = []
        for company in all_stocks['company']:
            if company in top_companies:
                marker_colors.append('#00cc96')
                marker_patterns.append('')
                marker_line_colors.append('#00cc96')
            elif company in bottom_companies:
                marker_colors.append('#ff4d4f')
                marker_patterns.append('')
                marker_line_colors.append('#ff4d4f')
            else:
                marker_colors.append('#d9d9d9')
                marker_patterns.append('/')
                marker_line_colors.append('#d9d9d9')

        logger.debug("Setting theme colors")
        if theme == 'dark':
            text_color = '#E0E0E0'
            grid_color = 'rgba(255, 255, 255, 0.2)'
            plot_bgcolor = '#1A252F'
            paper_bgcolor = '#1A252F'
        else:
            text_color = '#333333'
            grid_color = 'rgba(200, 200, 200, 0.2)'
            plot_bgcolor = '#F5F5F5'
            paper_bgcolor = '#FFFFFF'

        logger.debug("Creating Plotly figure")
        combined_fig = go.Figure()
        combined_fig.add_trace(go.Bar(
            x=all_stocks['company'],
            y=all_stocks['recommendation_score'],
            marker=dict(
                color=marker_colors,
                pattern=dict(shape=marker_patterns, solidity=0.3),
                line=dict(color=marker_line_colors, width=2)
            ),
            text=all_stocks['recommendation_score'].apply(
                lambda x: f'{float(x):.2f}' if pd.notnull(x) and isinstance(x, (int, float)) else '0.00'
            ),
            textposition='outside',
            textfont=dict(color=text_color, size=10),
            hovertemplate='<b>%{x}</b><br>Recommendation Score: %{y:.2f}<br>Category: %{customdata}<extra></extra>',
            customdata=all_stocks['category'],
            opacity=1.0,
            width=0.6
        ))
        combined_fig.update_layout(
            title={'text': 'Recommendation Scores for All Stocks', 'y': 0.95, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 18, 'color': text_color}},
            xaxis_title="Company",
            yaxis_title="Recommendation Score (0-1)",
            xaxis={
                'tickfont': {'size': 10, 'color': text_color},
                'showgrid': False,
                'zeroline': False,
                'automargin': True,
                'title': {'font': {'color': text_color}},
                'tickangle': 45
            },
            yaxis={
                'range': [0, 1.1],
                'tickfont': {'size': 12, 'color': text_color},
                'gridcolor': grid_color,
                'zeroline': False,
                'title': {'font': {'color': text_color}},
            },
            plot_bgcolor=plot_bgcolor,
            paper_bgcolor=paper_bgcolor,
            margin=dict(l=50, r=50, t=70, b=100),
            font=dict(family="Arial", size=12, color=text_color),
            showlegend=False,
            width=len(all_stocks) * 50,
            height=600,
            bargap=0.2,
            hovermode='closest',
            template=None
        )

        logger.debug("Serializing Plotly figure to JSON")
        result = {'combined_stocks': json.loads(plotly.io.to_json(combined_fig))}
        logger.debug(f"Graph data generated: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in create_recommendation_graphs: {str(e)}", exc_info=True)
        return {}

@app.route('/api/run_prediction', methods=['POST'])
@login_required
def run_prediction():
    try:
        data = request.json
        horizon = data.get('horizon', 7)
        current_week = datetime.now().strftime("%Y%m%d")
        predictions_collection = model.db["weekly_predictions"]
        existing_predictions = predictions_collection.find_one({"week_date": current_week, "horizon": horizon})
        
        force_update = False
        if existing_predictions:
            last_prediction_time = existing_predictions.get("last_updated", datetime.min)
            time_since_last_update = datetime.now() - last_prediction_time
            if time_since_last_update > timedelta(days=1):
                logger.info(f"Existing predictions for horizon {horizon} and week {current_week} are older than 1 day. Forcing update.")
                force_update = True
            else:
                global last_data_update
                if last_data_update and last_data_update <= last_prediction_time:
                    logger.info(f"Reusing existing predictions for horizon {horizon} and week {current_week}")
                    return jsonify({'success': True, 'message': f'Using cached predictions for {horizon} day horizon'}), 200
                else:
                    logger.info(f"last_data_update ({last_data_update}) is newer than last_prediction_time ({last_prediction_time}). Forcing update.")
                    force_update = True
        
        if existing_predictions and not force_update:
            logger.info(f"Reusing existing predictions for horizon {horizon} and week {current_week}")
            return jsonify({'success': True, 'message': f'Using cached predictions for {horizon} day horizon'}), 200

        logger.info(f"Running new predictions for horizon {horizon} and week {current_week}")
        updated_companies = 0
        failed_companies = []
        
        for company in nifty50.nifty_companies:
            logger.debug(f"Generating prediction for company: {company}")
            prediction_data = model.get_company_prediction(company, horizon)
            logger.debug(f"Prediction data for {company}: {prediction_data}")
            
            if prediction_data.get("success"):
                prediction = prediction_data.get("prediction", {})
                predicted_growth_score = prediction.get("predicted_growth_score", 0)
                recommendation_score = prediction.get("recommendation_score", 0)
                logger.debug(f"Extracted scores for {company} - predicted_growth_score: {predicted_growth_score}, recommendation_score: {recommendation_score}")
                
                predictions_collection.update_one(
                    {"company": company, "week_date": current_week, "horizon": horizon},
                    {
                        "$set": {
                            "metrics": prediction,
                            "predicted_growth_score": float(predicted_growth_score),
                            "recommendation_score": float(recommendation_score),
                            "last_updated": datetime.now()
                        }
                    },
                    upsert=True
                )
                updated_companies += 1
                logger.debug(f"Successfully updated prediction for {company}")
            else:
                error_message = prediction_data.get('error', 'Unknown error')
                logger.warning(f"Failed to get prediction for {company}: {error_message}")
                failed_companies.append(company)
                predictions_collection.update_one(
                    {"company": company, "week_date": current_week, "horizon": horizon},
                    {
                        "$set": {
                            "metrics": {},
                            "predicted_growth_score": 0.0,
                            "recommendation_score": 0.0,
                            "last_updated": datetime.now()
                        }
                    },
                    upsert=True
                )
        
        logger.info(f"Prediction update completed: {updated_companies} companies updated successfully, {len(failed_companies)} failed: {failed_companies}")
        return jsonify({
            'success': True,
            'message': f'Prediction completed for {horizon} day horizon. Updated {updated_companies} companies, failed {len(failed_companies)}.',
            'failed_companies': failed_companies
        }), 200
    except Exception as e:
        logger.error(f"Error in /api/run_prediction: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/scrape_news', methods=['POST'])
@login_required
def scrape_news():
    try:
        data = request.json
        company = data.get('company')
        scraped_news = [
            {"title": "NIFTY 50 rises on banking boost", "summary": "Banking sector led gains today.", "link": "http://example.com", "source": "NewsX", "datetime": "2025-05-01 10:00:00"},
            {"title": "Market dips slightly", "summary": "Minor correction seen in NIFTY 50.", "link": "http://example2.com", "source": "FinanceNews", "datetime": "2025-05-01 09:00:00"}
        ]
        model.store_scraped_news(company, scraped_news)
        global last_data_update
        last_data_update = datetime.now()
        return jsonify({'success': True, 'message': f'Scraped and stored news for {company}'}), 200
    except Exception as e:
        logger.error(f"Error in /api/scrape_news: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/companies', methods=['GET'])
def get_companies():
    try:
        companies = [
            {
                "ticker": ticker,
                "name": nifty50.get_full_name(ticker),
                "sector": nifty50.get_sector(ticker)
            }
            for ticker in nifty50.nifty_companies
            if ticker != "NIFTY 50"
        ]
        return jsonify({'companies': companies}), 200
    except Exception as e:
        logger.error(f"Error in /api/companies: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/sectors', methods=['GET'])
def get_sectors():
    try:
        sectors = sorted(set(
            nifty50.get_sector(ticker)
            for ticker in nifty50.nifty_companies
            if ticker != "NIFTY 50"
        ))
        return jsonify({'sectors': sectors}), 200
    except Exception as e:
        logger.error(f"Error in /api/sectors: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

def create_prediction_graphs(prediction_data, company):
    predicted_growth = prediction_data.get('predicted_growth_score', 0)
    previous_growth = prediction_data.get('previous_predicted_growth_score', predicted_growth * 0.9)
    recommendation_score = prediction_data.get('recommendation_score', 0)

    growth_fig = go.Figure()
    growth_fig.add_trace(go.Bar(
        x=['Current Score', 'Previous Score'],
        y=[predicted_growth, previous_growth],
        marker_color=['#00cc96', '#007bff'],
        text=[f'{predicted_growth:.2f}', f'{previous_growth:.2f}'],
        textposition='auto',
        hoverinfo='text',
        hovertext=[f'Current Score: {predicted_growth:.2f}', f'Previous Score: {previous_growth:.2f}']
    ))
    growth_fig.update_layout(
        title={'text': f"{company} Growth Score Comparison", 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'yanchor': 'top', 'font': {'size': 16, 'color': '#E0E0E0'}},
        xaxis_title="Period",
        yaxis_title="Growth Score (0-1)",
        xaxis={'tickfont': {'size': 12, 'color': '#E0E0E0'}},
        yaxis={'tickfont': {'size': 12, 'color': '#E0E0E0'}, 'range': [0, 1]},
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=50, r=50, t=50, b=50),
        font=dict(family="Arial", size=12, color="#E0E0E0")
    )
    
    rec_fig = go.Figure()
    rec_fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=recommendation_score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"{company} Recommendation Score", 'font': {'size': 16, 'color': '#E0E0E0'}},
        gauge={
            'axis': {'range': [0, 1], 'tickwidth': 1, 'tickcolor': "#E0E0E0"},
            'bar': {'color': "#007bff"},
            'steps': [
                {'range': [0, 0.33], 'color': "#ff4d4f"},
                {'range': [0.33, 0.66], 'color': "#ffd666"},
                {'range': [0.66, 1], 'color': "#00cc96"}
            ],
            'threshold': {'line': {'color': "red", 'width': 4}, 'thickness': 0.75, 'value': 0.5}
        },
        number={'font': {'size': 24, 'color': '#E0E0E0'}}
    ))
    rec_fig.update_layout(
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Arial", size=12, color="#E0E0E0"),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    return {
        'growth_comparison': json.loads(plotly.io.to_json(growth_fig)),
        'recommendation_gauge': json.loads(plotly.io.to_json(rec_fig))
    }

@app.route('/api/recommendations', methods=['GET'])
@login_required
def get_recommendations():
    try:
        theme = request.args.get('theme', default='dark', type=str)
        if theme not in ['dark', 'light']:
            theme = 'dark'

        recommendations = model.get_recommendations(horizon=7)
        if not recommendations.get("success"):
            return jsonify({'error': recommendations.get('error', 'No recommendations available')}), 404

        top_stocks = pd.DataFrame(recommendations.get('top_stocks', []))
        bottom_stocks = pd.DataFrame(recommendations.get('bottom_stocks', []))
        top_stocks = top_stocks.drop(columns=['_id'], errors='ignore')
        bottom_stocks = bottom_stocks.drop(columns=['_id'], errors='ignore')

        all_stocks = pd.DataFrame([
            {'company': c, 'recommendation_score': top_stocks[top_stocks['company'] == c]['recommendation_score'].iloc[0] if c in top_stocks['company'].values else 0.5, 'category': 'Top Recommendations'}
            for c in top_stocks['company']
        ] + [
            {'company': c, 'recommendation_score': bottom_stocks[bottom_stocks['company'] == c]['recommendation_score'].iloc[0] if c in bottom_stocks['company'].values else 0.5, 'category': 'Stocks to Avoid'}
            for c in bottom_stocks['company']
        ] + [
            {'company': c, 'recommendation_score': 0.5, 'category': 'Other Stocks'}
            for c in nifty50.nifty_companies if c not in top_stocks['company'].values and c not in bottom_stocks['company'].values
        ])

        graph_data = create_recommendation_graphs(top_stocks, bottom_stocks, all_stocks, theme=theme)
        if not graph_data:
            logger.warning("Failed to generate recommendation graphs")
            graph_data = {}

        response = {
            'top_stocks': sanitize_json(top_stocks.to_dict(orient='records')),
            'bottom_stocks': sanitize_json(bottom_stocks.to_dict(orient='records')),
            'graphs': sanitize_json(graph_data)
        }

        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error in /api/recommendations: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/stock_table', methods=['GET'])
@login_required
def get_stock_table():
    try:
        sector_filter = request.args.get('sector', default=None, type=str)
        companies = nifty50.nifty_companies
        stock_data = []
        current_week = datetime.now().strftime("%Y%m%d")
        try:
            predictions_collection = model.db["weekly_predictions"]
            predictions = predictions_collection.find({"week_date": current_week})
            prediction_dict = {pred["company"]: pred for pred in predictions}
        except Exception as e:
            logger.error(f"Error fetching predictions for week {current_week}: {str(e)}", exc_info=True)
            return jsonify({'error': f"Failed to fetch predictions: {str(e)}"}), 500
        for company in companies:
            if sector_filter and company != "NIFTY 50" and nifty50.get_sector(company) != sector_filter:
                continue
            if company == "NIFTY 50":
                continue
            financial_data = model.get_company_data(company)
            if not financial_data.get("success"):
                logger.warning(f"Skipping {company}: No financial data - {financial_data.get('error')}")
                continue
            stock = financial_data.get("stock_data", {})
            pred = prediction_dict.get(company, {})
            metrics = pred.get("metrics", {})
            ltp = float(stock.get("ltp", 0.0))
            if ltp == 0.0:
                logger.warning(f"Skipping {company}: Invalid LTP ({ltp})")
                continue
            stock_entry = {
                "company": company,
                "full_name": stock.get("company_name", nifty50.get_full_name(company)) or "Unknown",
                "sector": nifty50.get_sector(company),
                "ltp": ltp,
                "change": float(stock.get("change", 0.0)),
                "percent_change": float(stock.get("percent_change", 0.0)),
                "predicted_growth_score": float(pred.get("predicted_growth_score", 0.0)),
                "recommendation_score": float(pred.get("recommendation_score", 0.0)),
                "open_price": float(stock.get("open_price", ltp)),
                "high": float(stock.get("high", ltp)),
                "low": float(stock.get("low", ltp)),
                "prev_close": float(stock.get("prev_close", ltp)),
                "volume": float(metrics.get("volume", stock.get("volume", 1000000))),
                "value": float(stock.get("value", 0.0)),
                "week_high": float(metrics.get("week_high", stock.get("week_high", ltp * 1.1))),
                "week_low": float(metrics.get("week_low", stock.get("week_low", ltp * 0.9))),
                "30_d_percent_change": float(stock.get("30_d_percent_change", 0.0)),
                "pe_ratio": float(metrics.get("pe_ratio", stock.get("pe_ratio", 20.0))),
                "pb_ratio": float(metrics.get("pb_ratio", stock.get("pb_ratio", 3.0))),
                "ev_ebitda": float(metrics.get("ev_ebitda", stock.get("ev_ebitda", 10.0))),
                "market_cap": float(stock.get("market_cap", 100000)),
                "market_cap_tier": metrics.get("market_cap_tier", "Mid-cap"),
                "volatility": float(metrics.get("volatility", 0.3)),
                "beta": float(metrics.get("beta", 1.0))
            }
            critical_fields = ["ltp", "change", "percent_change", "volume", "open_price"]
            invalid_fields = [field for field in critical_fields if stock_entry[field] == 0.0]
            if invalid_fields:
                logger.warning(f"Invalid fields for {company}: {invalid_fields}")
            stock_data.append(stock_entry)
        if not stock_data:
            logger.error("No valid stock data available")
            return jsonify({'error': 'No valid stock data available'}), 500
        return jsonify({"stocks": sanitize_json(stock_data)}), 200
    except Exception as e:
        logger.error(f"Error in /api/stock_table: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)