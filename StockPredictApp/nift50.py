class Nifty50:
    def __init__(self):
        self.companies = {
            "NIFTY 50": {"name": "NIFTY 50 Index", "sector": "Index"},
            "SBILIFE": {"name": "SBI Life Insurance Company Ltd.", "sector": "Insurance"},
            "TECHM": {"name": "Tech Mahindra Ltd.", "sector": "IT"},
            "TCS": {"name": "Tata Consultancy Services Ltd.", "sector": "IT"},
            "INFY": {"name": "Infosys Ltd.", "sector": "IT"},
            "ULTRACEMCO": {"name": "UltraTech Cement Ltd.", "sector": "Cement"},
            "HINDUNILVR": {"name": "Hindustan Unilever Ltd.", "sector": "FMCG"},
            "GRASIM": {"name": "Grasim Industries Ltd.", "sector": "Diversified"},
            "INDUSINDBK": {"name": "IndusInd Bank Ltd.", "sector": "Banking"},
            "ICICIBANK": {"name": "ICICI Bank Ltd.", "sector": "Banking"},
            "RELIANCE": {"name": "Reliance Industries Ltd.", "sector": "Energy"},
            "HDFCBANK": {"name": "HDFC Bank Ltd.", "sector": "Banking"},
            "ITC": {"name": "ITC Ltd.", "sector": "FMCG"},
            "HCLTECH": {"name": "HCL Technologies Ltd.", "sector": "IT"},
            "TITAN": {"name": "Titan Company Ltd.", "sector": "Consumer Durables"},
            "HDFCLIFE": {"name": "HDFC Life Insurance Company Ltd.", "sector": "Insurance"},
            "WIPRO": {"name": "Wipro Ltd.", "sector": "IT"},
            "NESTLEIND": {"name": "Nestlé India Ltd.", "sector": "FMCG"},
            "LT": {"name": "Larsen & Toubro Ltd.", "sector": "Construction"},
            "TATACONSUM": {"name": "Tata Consumer Products Ltd.", "sector": "FMCG"},
            "KOTAKBANK": {"name": "Kotak Mahindra Bank Ltd.", "sector": "Banking"},
            "SUNPHARMA": {"name": "Sun Pharmaceutical Industries Ltd.", "sector": "Pharmaceuticals"},
            "M&M": {"name": "Mahindra & Mahindra Ltd.", "sector": "Automobile"},
            "HINDALCO": {"name": "Hindalco Industries Ltd.", "sector": "Metals"},
            "ONGC": {"name": "Oil & Natural Gas Corporation Ltd.", "sector": "Energy"},
            "ASIANPAINT": {"name": "Asian Paints Ltd.", "sector": "Paints"},
            "EICHERMOT": {"name": "Eicher Motors Ltd.", "sector": "Automobile"},
            "BHARTIARTL": {"name": "Bharti Airtel Ltd.", "sector": "Telecom"},
            "CIPLA": {"name": "Cipla Ltd.", "sector": "Pharmaceuticals"},
            "COALINDIA": {"name": "Coal India Ltd.", "sector": "Mining"},
            "SBIN": {"name": "State Bank of India", "sector": "Banking"},
            "HEROMOTOCO": {"name": "Hero MotoCorp Ltd.", "sector": "Automobile"},
            "MARUTI": {"name": "Maruti Suzuki India Ltd.", "sector": "Automobile"},
            "TATASTEEL": {"name": "Tata Steel Ltd.", "sector": "Metals"},
            "TATAMOTORS": {"name": "Tata Motors Ltd.", "sector": "Automobile"},
            "NTPC": {"name": "NTPC Ltd.", "sector": "Power"},
            "JSWSTEEL": {"name": "JSW Steel Ltd.", "sector": "Metals"},
            "BAJAJ-AUTO": {"name": "Bajaj Auto Ltd.", "sector": "Automobile"},
            "BAJFINANCE": {"name": "Bajaj Finance Ltd.", "sector": "Finance"},
            "DRREDDY": {"name": "Dr. Reddy's Laboratories Ltd.", "sector": "Pharmaceuticals"},
            "JIOFIN": {"name": "Jio Financial Services Ltd.", "sector": "Finance"},
            "BEL": {"name": "Bharat Electronics Ltd.", "sector": "Defense"},
            "BAJAJFINSV": {"name": "Bajaj Finserv Ltd.", "sector": "Finance"},
            "POWERGRID": {"name": "Power Grid Corporation of India Ltd.", "sector": "Power"},
            "APOLLOHOSP": {"name": "Apollo Hospitals Enterprise Ltd.", "sector": "Healthcare"},
            "AXISBANK": {"name": "Axis Bank Ltd.", "sector": "Banking"},
            "ETERNAL": {"name": "Eternal Capital", "sector": "Financial Services"},
            "TRENT": {"name": "Trent Ltd.", "sector": "Retail"},
            "ADANIPORTS": {"name": "Adani Ports and Special Economic Zone Ltd.", "sector": "Logistics"},
            "ADANIENT": {"name": "Adani Enterprises Ltd.", "sector": "Conglomerate"},
            "SHRIRAMFIN": {"name": "Shriram Finance Ltd.", "sector": "Finance"},
        }

        self.company_name_to_ticker = {
            info["name"]: ticker for ticker, info in self.companies.items()
        }
        self.nifty_companies = list(self.companies.keys())

    def get_full_name(self, ticker):
        return self.companies.get(ticker, {}).get("name", ticker)

    def get_sector(self, ticker):
        return self.companies.get(ticker, {}).get("sector", "Unknown")

    def get_ticker(self, full_name):
        return self.company_name_to_ticker.get(full_name, full_name)
