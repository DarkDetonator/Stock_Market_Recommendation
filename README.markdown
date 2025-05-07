# Stock Prediction Application

<p align="center">
  <img src="https://github.com/user-attachments/assets/678ef3df-5803-46ec-8ada-fbeac0eb1a09" alt="Screenshot 2025-05-07 182238" width="600"/>
</p>


##  Overview
This repository hosts a Flask-based web application for stock prediction, leveraging the **XGBoost** machine learning model. The project encompasses:

- Data extraction from *NSE* and *Moneycontrol*
- Synthetic data generation
- Model training and hyperparameter tuning
- A user-friendly interface with login functionality

It provides stock recommendations, growth scores, and financial calculations for companies, including those in the **Nifty 50** index.

![68747470733a2f2f692e696d6775722e636f6d2f77617856496d762e706e67](https://github.com/user-attachments/assets/9b8974ab-4aa6-41f6-998c-5021ae4499d3)


##  Project Structure
- **`web_Scraping/`**: Scripts for data extraction.  
  - `mony_contol.py`: Scrapes data from Moneycontrol.  
  - `nse_extraction.py`: Scrapes data from NSE. 
- **`generatingSyntheticData/`**: Scripts for data extraction and generation.  
  - `insert_into_db.py`: Inserts data into the database.  
  - `synthetic_data.py`: Generates synthetic data when real data is insufficient.  
- **`horizon_Prediction/`**: Model training and hyperparameter tuning.  
  - `XGBoostModel.py`: Implements the XGBoost model for predictions.  
- **`StockPredictApp/`**: Core application for stock prediction.  
  - `login/`: Manages user authentication.  
  - `app.py`: Hosts the Flask application server.  
  - `model.py`: Retrieves company data and stock details.  
  - `nifty50.py`: Fetches names of Nifty 50 companies.  
  - `stock_predictor.py`: XGBoost model for predictions, growth scores, and recommendations.  
- **`requirements.txt`**: Lists required Python packages.  

![68747470733a2f2f692e696d6775722e636f6d2f77617856496d762e706e67](https://github.com/user-attachments/assets/9b8974ab-4aa6-41f6-998c-5021ae4499d3)

## Prerequisites
Before starting, ensure you have the following:

- **Python 3.8+**  
- **MySQL** or another compatible database for storing stock data  
- **Virtual Environment** (recommended)  

---

## Installation

Follow these steps to set up the project:

1. **Clone the Repository**  
   Run the following commands to clone the repository:

   ```bash
   git clone = https://github.com/DarkDetonator/Stock_Market_Recommendation.git
   cd stock-prediction-app
   ```

2. **Set Up a Virtual Environment**  
   Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   On Windows, use:

   ```bash
   venv\Scripts\activate
   ```

3. **Install Dependencies**  
   Install the required packages listed in `requirements.txt`:

   ```bash
   pip install pip install -r requirements.txt
   ```

4. **Configure the Database**  
   - Set up a MySQL database.  
   - Update the database connection details in `generatingSyntheticData/insert_into_db.py` and other relevant scripts.  

---

##  Usage

### 1. Start the Login Server
> **Note**: The login server must be started first as it is interconnected with the main application.

Navigate to the `login/` directory and start the server:

```bash
cd StockPredictApp/login
python login_server.py
# Replace with the actual login server script name if different
```

Ensure the login server is running before proceeding.

### 2. Start the Main Application
Return to the parent directory and start the main application:

```bash
cd ..
python app.py
```

Access the application at `http://localhost:5000` (or the configured port).

### 3. Data Extraction and Synthetic Data Generation
Follow these sub-steps:

1. **Scrape Data** from NSE and Moneycontrol:  
   Navigate to the `web_Scraping/` directory and run the scripts:

   ```bash
   cd web_Scraping
   python nse_extraction.py
   python mony_contol.py
   ```

2. **Generate Synthetic Data** if real data is insufficient:  
   Navigate to the `generatingSyntheticData/` directory and run the script:

   ```bash
   cd ../generatingSyntheticData
   python synthetic_data.py
   ```

3. **Insert Data** into the database:  
   Insert the scraped or synthetic data into the database:

   ```bash
   python insert_into_db.py
   ```

### 4. Model Training and Hyperparameter Tuning
Train the XGBoost model and tune hyperparameters:

```bash
cd horizon_Prediction
python XGBoostModel.py
```

---

##  Features
- **Data Extraction**: Scrapes real-time stock data from *NSE* and *Moneycontrol*.  
- **Synthetic Data Generation**: Generates synthetic data when real data is insufficient.  
- **Stock Prediction**: Uses `XGBoost` to predict stock trends and calculate growth scores.  
- **Nifty 50 Support**: Fetches and analyzes data for Nifty 50 companies.  
- **User Interface**: Flask-based web app with secure login functionality.  
- **Recommendations**: Provides stock recommendations based on ML predictions.  

---

##  Contributing
Contributions are welcome! Here’s how you can contribute:

1. Fork the repository.
2. Create a new branch for your changes.
3. Make your changes and commit them.
4. Submit a pull request.

Ensure your code adheres to [PEP 8](https://www.python.org/dev/peps/pep-0008/) guidelines and includes proper documentation.

---

##  License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## 📧 Contact
For questions or issues, please open an issue on the [https://github.com/DarkDetonator/Stock_Market_Recommendation/issues) or contact the repository owner at `JosephJaison629@gmail.com`.

---

