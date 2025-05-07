from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from flask_cors import CORS
import bcrypt
from pymongo import MongoClient
import logging
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)  # Enable CORS for potential frontend integration
app.secret_key = 'simple-session-key'  # Required for Flask sessions
app.permanent_session_lifetime = timedelta(days=1)  # Session expiry

# MongoDB setup
MONGO_URI = 'mongodb://localhost:27017'  # Replace with your MongoDB URI
DB_NAME = 'auth_db'
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
users_collection = db['users']

# Logging setup
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Helper Functions
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password)

# Routes
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect('http://localhost:5000')  # Redirect to main app
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect('http://localhost:5000')
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return render_template('login.html', error='Missing required fields')

        user = users_collection.find_one({'email': email})
        if not user or not verify_password(password, user['password']):
            return render_template('login.html', error='Invalid email or password')

        session.permanent = True
        session['user_id'] = str(user['_id'])
        session['username'] = user['username']
        logger.info(f"User logged in: {email}")
        return redirect('http://localhost:5000')
    
    return render_template('login.html', error=None)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect('http://localhost:5000')
    if request.method == 'POST':
        data = request.form
        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        if not all([email, username, password]):
            return render_template('register.html', error='Missing required fields')

        if users_collection.find_one({'email': email}):
            return render_template('register.html', error='Email already registered')

        hashed_password = hash_password(password)
        user = {
            'email': email,
            'username': username,
            'password': hashed_password,
            'created_at': datetime.utcnow()
        }
        result = users_collection.insert_one(user)
        session.permanent = True
        session['user_id'] = str(result.inserted_id)
        session['username'] = username
        logger.info(f"User registered: {email}")
        return redirect('http://localhost:5000')
    
    return render_template('register.html', error=None)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)