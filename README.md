Stock Prediction Application
Overview
This repository contains a Flask-based web application for stock prediction using the XGBoost machine learning model. The project includes data extraction from NSE and Moneycontrol, synthetic data generation, model training, hyperparameter tuning, and a user-friendly interface with login functionality. The application provides stock recommendations, growth scores, and other financial calculations for companies, including those in the Nifty 50 index.
Project Structure

generatingSyntheticData/: Scripts for extracting and generating data.
insert_into_db.py: Inserts data into the database.
synthetic_data.py: Generates synthetic data when real data is insufficient.


horizon_Prediction/: Model training and hyperparameter tuning.
XGBoostModel.py: Contains the XGBoost model implementation for predictions.


StockPredictApp/: Main application for stock prediction.
login/: Handles user authentication.
app.py: Flask application hosting the main server.
model.py: Fetches company data and stock details.
nifty50.py: Class to fetch names of Nifty 50 companies.
stock_predictor.py: XGBoost model for predictions, growth scores, and recommendations.


web_Scraping/: Data extraction scripts.
mony_contol.py: Scrapes data from Moneycontrol.
nse_extraction.py: Scrapes data from NSE.


requirements.txt: Lists all required Python packages.

Prerequisites

Python 3.8+
MySQL or another compatible database for storing stock data
Virtual environment (recommended)

Installation

Clone the Repository:
git clone https://github.com/your-username/stock-prediction-app.git
cd stock-prediction-app


Set Up a Virtual Environment:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


Install Dependencies:
pip install -r requirements.txt


Configure the Database:

Set up a MySQL database.
Update the database connection details in generatingSyntheticData/insert_into_db.py and any other relevant scripts.



Usage

Start the Login Server:

The login server must be started first as it is interconnected with the main application.

cd StockPredictApp/login
python login_server.py  # Replace with the actual login server script name if different


Ensure the login server is running before proceeding.


Start the Main Application:
cd ../
python app.py


Access the application at http://localhost:5000 (or the configured port).


Data Extraction and Synthetic Data Generation:

Run the web scraping scripts to fetch data from NSE and Moneycontrol:cd web_Scraping
python nse_extraction.py
python mony_contol.py


If data is insufficient, generate synthetic data:cd ../generatingSyntheticData
python synthetic_data.py


Insert the data into the database:python insert_into_db.py




Model Training and Hyperparameter Tuning:

Train the XGBoost model and tune hyperparameters:cd horizon_Prediction
python XGBoostModel.py





Features

Data Extraction: Scrapes real-time stock data from NSE and Moneycontrol.
Synthetic Data Generation: Generates synthetic data when real data is insufficient.
Stock Prediction: Uses an XGBoost model to predict stock trends and calculate growth scores.
Nifty 50 Support: Fetches and analyzes data for Nifty 50 companies.
User Interface: Flask-based web app with login functionality for secure access.
Recommendations: Provides stock recommendations based on ML predictions.

Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes. Ensure your code follows PEP 8 guidelines and includes appropriate documentation.
License
This project is licensed under the MIT License. See the LICENSE file for details.
Contact
For any questions or issues, please open an issue on GitHub or contact the repository owner at your-email@example.com.
