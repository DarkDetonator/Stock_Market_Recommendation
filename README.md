Stock Prediction Application
📋 Overview
This repository hosts a Flask-based web application for stock prediction, leveraging the XGBoost machine learning model. The project encompasses data extraction from NSE and Moneycontrol, synthetic data generation, model training, hyperparameter tuning, and a user-friendly interface with login functionality. It provides stock recommendations, growth scores, and financial calculations for companies, including those in the Nifty 50 index.

📂 Project Structure

generatingSyntheticData/: Scripts for data extraction and generation.  
insert_into_db.py: Inserts data into the database.  
synthetic_data.py: Generates synthetic data when real data is insufficient.


horizon_Prediction/: Model training and hyperparameter tuning.  
XGBoostModel.py: Implements the XGBoost model for predictions.


StockPredictApp/: Core application for stock prediction.  
login/: Manages user authentication.  
app.py: Hosts the Flask application server.  
model.py: Retrieves company data and stock details.  
nifty50.py: Fetches names of Nifty 50 companies.  
stock_predictor.py: XGBoost model for predictions, growth scores, and recommendations.


web_Scraping/: Scripts for data extraction.  
mony_contol.py: Scrapes data from Moneycontrol.  
nse_extraction.py: Scrapes data from NSE.


requirements.txt: Lists required Python packages.


🛠️ Prerequisites

Python 3.8+  
MySQL or another compatible database for storing stock data  
Virtual Environment (recommended)


🚀 Installation
Step 1: Clone the Repository
git clone https://github.com/your-username/stock-prediction-app.git
cd stock-prediction-app

Step 2: Set Up a Virtual Environment
python -m venv venv
source venv/bin/activate
# On Windows: venv\Scripts\activate

Step 3: Install Dependencies
pip install -r requirements.txt

Step 4: Configure the Database

Set up a MySQL database.  
Update the database connection details in generatingSyntheticData/insert_into_db.py and other relevant scripts.


📖 Usage
1. Start the Login Server

Note: The login server must be started first as it is interconnected with the main application.

cd StockPredictApp/login
python login_server.py
# Replace with the actual login server script name if different

Ensure the login server is running before proceeding.
2. Start the Main Application
cd ..
python app.py

Access the application at http://localhost:5000 (or the configured port).
3. Data Extraction and Synthetic Data Generation

Scrape Data from NSE and Moneycontrol:

cd web_Scraping
python nse_extraction.py
python mony_contol.py


Generate Synthetic Data if real data is insufficient:

cd ../generatingSyntheticData
python synthetic_data.py


Insert Data into the database:

python insert_into_db.py

4. Model Training and Hyperparameter Tuning
Train the XGBoost model and tune hyperparameters:  
cd horizon_Prediction
python XGBoostModel.py


✨ Features

Data Extraction: Scrapes real-time stock data from NSE and Moneycontrol.  
Synthetic Data Generation: Generates synthetic data when real data is insufficient.  
Stock Prediction: Uses XGBoost to predict stock trends and calculate growth scores.  
Nifty 50 Support: Fetches and analyzes data for Nifty 50 companies.  
User Interface: Flask-based web app with secure login functionality.  
Recommendations: Provides stock recommendations based on ML predictions.


🤝 Contributing
Contributions are welcome! Please fork the repository, create a new branch, and submit a pull request with your changes. Ensure your code adheres to PEP 8 guidelines and includes proper documentation.

📜 License
This project is licensed under the MIT License. See the LICENSE file for details.

📧 Contact
For questions or issues, please open an issue on GitHub or contact the repository owner at your-email@example.com.

⚠️ Troubleshooting Rendering Issues
If the code blocks do not render correctly on GitHub (e.g., they appear as plain text or commands join into a single line), ensure the following:

The file uses Unix-style line endings (LF). If you're on Windows, convert the file to LF using a tool like dos2unix or your editor's settings.
There are no extra spaces or incorrect indentation around the code blocks (bash ... ).
View the README directly on GitHub to confirm rendering. If the issue persists, try re-uploading the file to GitHub.

