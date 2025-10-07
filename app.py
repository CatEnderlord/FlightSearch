from flask import Flask, render_template, request, jsonify, redirect, url_for
import csv
from math import radians, sin, cos, sqrt, atan2
import requests
import subprocess
import sys
import threading
import time
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Change this to a random secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # Set the login view for redirecting unauthorized users

# User model
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

# Create database tables
with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(id):
    return Users.query.get(int(id))

# AviationStack API configuration
API_KEY = "fb786006380d79f96d14a90de1d4c669"
API_URL = "https://api.aviationstack.com/v1/flights"

# Load the AIRPORTS data from a CSV file
AIRPORTS = []
def load_airports_from_csv(file_path):
    global AIRPORTS
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            AIRPORTS.append({
                "name": row["name"],
                "code": row["code"],
                "lat": float(row["lat"]),
                "lng": float(row["lng"])
            })

# Call this function to load the CSV file when the app starts
load_airports_from_csv("airports.csv")

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # Earth radius in kilometers
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def get_nearest_airport(lat, lng):
    nearest_airport = None
    min_distance = float('inf')

    for airport in AIRPORTS:
        distance = haversine(lat, lng, airport["lat"], airport["lng"])
        if distance < min_distance:
            min_distance = distance
            nearest_airport = airport

    return nearest_airport

# Authentication routes
@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('map'))
        else:
            print('Invalid username or password')
    return render_template("login.html")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if password1 != password2:
            print('Passwords do not match')
        elif len(password1) < 6 or len(username) < 6:
            print('Username or password is too short')
        elif Users.query.filter_by(username=username).first() or Users.query.filter_by(email=email).first():
            print('User already exists')
        else:
            new_user = Users(username=username, email=email, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('map'))
    return render_template("register.html")

@app.route('/index')
@login_required
def index():
    return render_template('index.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/tabel')
@login_required
def tabel():
    try:
        # Fetch flights data from the AviationStack API
        params = {
            'access_key': API_KEY,
            'limit': 50  # Limit the number of flights displayed in the table
        }
        response = requests.get(API_URL, params=params, timeout=10)
        data = response.json()

        # Check if the API response contains data and handle potential errors
        if 'data' in data:
            flights = data['data']
        else:
            flights = []
            error_message = data.get('error', {}).get('info', 'Unknown API error')
            print(f"API Error: {error_message}")
            
        return render_template('tabel.html', flights=flights)
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to flight API: {str(e)}")
        return render_template('tabel.html', flights=[])
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return render_template('tabel.html', flights=[])

# New route from flights_search for searching flights
@app.route('/search', methods=['POST'])
@login_required
def search():
    search_query = request.form.get('query', '')
    
    # Get filter values
    flight_status = request.form.get('flight_status', '')
    min_departure_time = request.form.get('min_departure_time', '')
    max_departure_time = request.form.get('max_departure_time', '')
    min_arrival_time = request.form.get('min_arrival_time', '')
    max_arrival_time = request.form.get('max_arrival_time', '')
    
    # Parameters for the API request
    params = {
        'access_key': API_KEY,
    }
    
    # Add search parameters based on the query type
    if search_query:
        # Check if the query looks like a flight number (alphanumeric)
        if any(c.isalpha() for c in search_query) and any(c.isdigit() for c in search_query):
            params['flight_iata'] = search_query
        # Check if the query is all letters (likely an airport code)
        elif search_query.isalpha() and len(search_query) <= 3:
            # Try it as a departure or arrival airport
            params['dep_iata'] = search_query
        # Otherwise, try it as an airline name
        else:
            params['airline_name'] = search_query
    
    # Add filter parameters
    if flight_status:
        params['flight_status'] = flight_status
    
    # Add time filters if provided
    if min_departure_time:
        params['dep_scheduled_time_gt'] = min_departure_time
    if max_departure_time:
        params['dep_scheduled_time_lt'] = max_departure_time
    if min_arrival_time:
        params['arr_scheduled_time_gt'] = min_arrival_time
    if max_arrival_time:
        params['arr_scheduled_time_lt'] = max_arrival_time
    
    try:
        # Make the API request
        response = requests.get(API_URL, params=params)
        data = response.json()
        
        # Check if the request was successful
        if 'error' in data:
            return jsonify({'error': data['error']['info']})
        
        # Return the flights data
        return jsonify(data)
    
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/map')
@login_required
def map():
    params = {
        'access_key': API_KEY,
        'limit': 3000
    }
    response = requests.get(API_URL, params=params)
    data = response.json()
    flights = data.get('data', [])
    return render_template('index.html', flights=flights)

@app.route('/calculate')
@login_required
def calculate():
    start_lat = float(request.args.get('startLat'))
    start_lng = float(request.args.get('startLng'))
    end_lat = float(request.args.get('endLat'))
    end_lng = float(request.args.get('endLng'))

    start_airport = get_nearest_airport(start_lat, start_lng)
    end_airport = get_nearest_airport(end_lat, end_lng)

    if not start_airport or not end_airport:
        return jsonify({"error": "Could not find nearby airports."}), 400

    distance = haversine(
        start_airport["lat"], start_airport["lng"],
        end_airport["lat"], end_airport["lng"]
    )
    avg_speed = 900
    flight_time = distance / avg_speed

    return jsonify({
        "startAirport": start_airport,
        "endAirport": end_airport,
        "flightTime": round(flight_time, 2)
    })

if __name__ == '__main__':
    app.run(debug=True)