import os
import streamlit as st
import requests
import re
from datetime import datetime, timedelta
from groq import Groq
import google.generativeai as genai
from pathlib import Path
import sqlite3
import uuid
import hashlib
import time

# App configuration
st.set_page_config(
    page_title="HIDDEN HORIZONS",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    /* Primary colors */
    :root {
        --primary-color: #2E86C1;
        --secondary-color: #AED6F1;
        --accent-color: #F39C12;
        --dark-bg: #1E3A5F;
        --light-bg: #9EC6F3; /* Updated background color */
        --text-color: #2C3E50;
    }
    
    /* Main container styling */
    .main {
        background-color: var(--light-bg);
        padding: 20px;
        border-radius: 10px;
    }
    
    /* Header styling */
    h1, h2, h3 {
        color: var(--primary-color);
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Button styling */
    .stButton>button {
        background-color: #A62C2C; /* Updated button color */
        color: white;
        border-radius: 5px;
        padding: 10px 24px;
        font-weight: bold;
        border: none;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        background-color: var(--dark-bg);
        color: white;
    }
    
    /* Card styling */
    .css-card {
        border-radius: 10px;
        padding: 20px;
        background-color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Input styling */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stDateInput>div>div>input {
        border-radius: 5px;
        border: 1px solid #ccc;
        padding: 10px;
    }
    
    /* Sidebar styling */
    .css-sidebar {
        background-color: var(--primary-color);
        padding: 20px;
        border-radius: 10px;
        color: white;
    }
    
    /* Success message styling */
    .element-container:has(.stAlert) {
        padding: 10px;
        border-radius: 10px;
    }
    
    /* Navigation menu */
    .nav-link {
        text-decoration: none;
        color: var(--primary-color);
        font-weight: bold;
        margin-right: 20px;
        font-size: 16px;
    }
    
    .nav-link:hover {
        color: var(--accent-color);
    }
    
    /* Nav bar alignment fix */
    .navbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    
    .navbar-brand {
        display: flex;
        align-items: center;
    }
    
    .navbar-menu {
        display: flex;
        justify-content: flex-end;
        align-items: center;
        gap: 10px;
    }
    
    /* Fixed horizontal button layout */
    .navbar-menu .stButton {
        display: inline-block;
        margin-right: 10px !important;
    }
    
    .navbar-menu button {
        min-width: 100px;
    }
    
    /* Footer styling */
    .footer {
        text-align: center;
        padding: 20px;
        color: gray;
        font-size: 14px;
        margin-top: 50px;
    }
    
    /* Logo and branding */
    .logo-text {
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: bold;
        font-size: 24px;
        color: var(--primary-color);
    }
    
    /* Accommodation card */
    .accommodation-card {
        background-color: #f9f9f9;
        border-left: 5px solid var(--primary-color);
        padding: 15px;
        margin-bottom: 10px;
        border-radius: 5px;
    }
    
    /* Apply background color to entire app */
    body {
        background-color: var(--light-bg);
    }
</style>
""", unsafe_allow_html=True)

# 🔐 API Key Setup
os.environ["GROQ_API_KEY"] = "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"
WEATHER_API_KEY = "7f315248aa15f08e5d5e7cc256193ffd"
GEMINI_API_KEY = "AIzaSyCLzKZuHB5AJhyymndn_UhAD_BKPGmVkHo"

# Initialize API clients
client = Groq()
genai.configure(api_key=GEMINI_API_KEY)

# Database initialization and helper functions
def init_db():
    try:
        conn = sqlite3.connect('travel_planner.db', check_same_thread=False)
        c = conn.cursor()
        
        # Create users table
        c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        return conn
    except Exception as e:
        print(f"Database initialization error: {e}")
        return None

# Authentication helper functions
def hash_password(password):
    """Hash a password for storing."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(stored_password, provided_password):
    """Verify a stored password against a provided password"""
    return stored_password == hashlib.sha256(provided_password.encode()).hexdigest()

def register_user(conn, username, email, password):
    """Register a new user and return success status"""
    try:
        c = conn.cursor()
        user_id = str(uuid.uuid4())
        password_hash = hash_password(password)
        c.execute(
            "INSERT INTO users (user_id, username, email, password_hash) VALUES (?, ?, ?, ?)",
            (user_id, username, email, password_hash)
        )
        conn.commit()
        return True, user_id
    except sqlite3.IntegrityError as e:
        print(f"Registration error: {e}")
        return False, None

def login_user(conn, username, password):
    """Verify user credentials and return user_id if valid"""
    try:
        c = conn.cursor()
        c.execute("SELECT user_id, password_hash FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        
        if result and verify_password(result[1], password):
            return True, result[0]
        return False, None
    except Exception as e:
        print(f"Login error: {e}")
        return False, None

def check_user_exists(conn, username):
    """Check if a username exists in the database"""
    try:
        c = conn.cursor()
        c.execute("SELECT username, password_hash FROM users WHERE username = ?", (username,))
        result = c.fetchone()
        if result:
            return True, result[1]
        return False, None
    except Exception as e:
        print(f"Check user exists error: {e}")
        return False, None

# Initialize the database connection
conn = init_db()
if not conn:
    st.error("Failed to initialize database connection. Please check server logs.")
    st.stop()

# Initialize session state variables if they don't exist
if 'page' not in st.session_state:
    st.session_state.page = "login"
if 'trip_plan' not in st.session_state:
    st.session_state.trip_plan = None
if 'destination' not in st.session_state:
    st.session_state.destination = None
if 'weather' not in st.session_state:
    st.session_state.weather = None
if 'temp' not in st.session_state:
    st.session_state.temp = None
if 'accommodations' not in st.session_state:
    st.session_state.accommodations = None
if 'transport_options' not in st.session_state:
    st.session_state.transport_options = None
if 'is_architecture_student' not in st.session_state:
    st.session_state.is_architecture_student = False
if 'username' not in st.session_state:
    st.session_state.username = "Guest"
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'db_conn' not in st.session_state:
    st.session_state.db_conn = conn
if 'signup_success' not in st.session_state:
    st.session_state.signup_success = False
if 'login_error' not in st.session_state:
    st.session_state.login_error = False
if 'preferences' not in st.session_state:
    st.session_state.preferences = ""
if 'mood' not in st.session_state:
    st.session_state.mood = ""
if 'start_date' not in st.session_state:
    st.session_state.start_date = datetime.today().date()
if 'home_city' not in st.session_state:
    st.session_state.home_city = ""
if 'budget' not in st.session_state:
    st.session_state.budget = 10000
if 'trip_length' not in st.session_state:
    st.session_state.trip_length = 2

# Navigation Functions
def go_to_home():
    st.session_state.page = "home"
    
def go_to_results():
    st.session_state.page = "results"
    
def go_to_contact():
    st.session_state.page = "contact"

def go_to_login():
    st.session_state.page = "login"
    
def go_to_signup():
    st.session_state.page = "signup"

# ☁ Weather API
def get_weather(destination):
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={destination}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if response.status_code == 200 and data.get("weather"):
            return data["weather"][0]["description"], data["main"]["temp"]
        return "Weather data unavailable", 0
    except Exception as e:
        print(f"Weather API error: {e}")
        return "Weather data unavailable", 0

# 💬 Mood Analyzer
def analyze_mood(user_mood):
    if not user_mood:
        return "relaxation"
        
    messages = [
        {"role": "system", "content": "You are an emotion analysis AI. Categorize the user's mood into one of these: 'relaxation', 'adventure', 'celebration', 'healing', or 'exploration'."},
        {"role": "user", "content": f"My current mood is: {user_mood}"}
    ]
    try:
        result = client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
        return result.choices[0].message.content.strip()
    except Exception as e:
        print(f"Mood analysis error: {e}")
        return "relaxation"

# 📍 Destination Extractor
def extract_destination(text):
    if not text:
        return "Unknown"
        
    match = re.search(r"Destination[:\-]?\s*(.*)", text, re.IGNORECASE)
    if match:
        destination_line = match.group(1).strip()
        return destination_line.split('\n')[0].strip()
    match2 = re.search(r"to\s+([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)", text)
    return match2.group(1) if match2 else "Unknown"

# 🏨 Dynamic Accommodation
def get_cheapest_accommodation(destination, budget):
    if not destination or not budget:
        return [
            {"name": "Comfort Stay", "price": "₹2500/night", "link": "https://example.com/hotel1"},
            {"name": "Budget Inn", "price": "₹2000/night", "link": "https://example.com/hotel2"},
        ]
        
    max_price = budget * 0.3
    base_prices = {
        "Goa": [2600, 2200],
        "Manali": [1800, 1500],
        "Mysore": [2000, 1700],
        "Lonavala": [2100, 1900]
    }
    options = base_prices.get(destination, [2500, 2300])
    return [
        {"name": f"{destination} Comfort Stay", "price": f"₹{options[0]}/night", "link": "https://example.com/hotel1"},
        {"name": f"{destination} Budget Inn", "price": f"₹{options[1]}/night", "link": "https://example.com/hotel2"},
    ]

# 🚆 Dynamic Transport
def get_cheapest_transport(from_city, to_city, budget):
    if not from_city or not to_city or not budget:
        return [
            {"mode": "Train", "route": "City to Destination", "price": "₹600", "link": "https://www.irctc.co.in"},
            {"mode": "Bus", "route": "City to Destination", "price": "₹450", "link": "https://www.redbus.in"},
        ]
        
    max_price = budget * 0.3
    return [
        {"mode": "Train", "route": f"{from_city} to {to_city}", "price": f"₹{int(max_price * 0.2)}", "link": "https://www.irctc.co.in"},
        {"mode": "Bus", "route": f"{from_city} to {to_city}", "price": f"₹{int(max_price * 0.15)}", "link": "https://www.redbus.in"},
    ]

# 🧠 Main Planning
def plan_getaway(home_city, budget, preferences, mood, trip_length, max_travel_time, start_date, transport_mode, is_architecture_student):
    if not home_city or not budget or not preferences or not mood:
        return None, None, None, None, None, None
        
    sentiment_category = analyze_mood(mood)

    try:
        if isinstance(start_date, str):
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = datetime.today().date()
        
        if is_architecture_student:
            user_prompt = (
                f"I am an architecture student in {home_city} with a budget of ₹{budget}. I want a getaway from {start_date.strftime('%Y-%m-%d')} "
                f"to {(start_date + timedelta(days=trip_length)).strftime('%Y-%m-%d')}. My preferences: {preferences}. My current mood is: '{mood}', "
                f"so I need a trip focused on '{sentiment_category}'. Max travel time: {max_travel_time} hours. "
                f"My preferred mode of transportation is {transport_mode}. "
                "As an architecture student, I want to explore places with architectural significance, historical buildings, or unique urban planning. "
                "Recommend a destination with an itinerary including transport, activities focused on architectural exploration, food, and accommodation. "
                "Clearly mention the Destination.\n\n"
                "Also, please list 2-3 nearby architecture schools and colleges with:\n"
                "- Institution Name\n"
                "- Brief information about their architectural program\n"
                "- Email Address\n"
                "- Contact Number"
            )
        else:
            user_prompt = (
                f"I am in {home_city} with a budget of ₹{budget}. I want a getaway from {start_date.strftime('%Y-%m-%d')} "
                f"to {(start_date + timedelta(days=trip_length)).strftime('%Y-%m-%d')}. My preferences: {preferences}. My current mood is: '{mood}', "
                f"so I need a trip focused on '{sentiment_category}'. Max travel time: {max_travel_time} hours. "
                f"My preferred mode of transportation is {transport_mode}. "
                "Recommend a great destination with an itinerary including transport, activities, food, and accommodation. "
                "Clearly mention the Destination.\n\n"
                "Also, please list 2–3 nearby colleges or schools in that destination with:\n"
                "- Institution Name\n"
                "- Email Address\n"
                "- Contact Number"
            )

        messages = [
            {"role": "system", "content": "You are an AI travel planner specializing in emotionally intelligent weekend getaways."},
            {"role": "user", "content": user_prompt}
        ]
        
        response = client.chat.completions.create(model="llama-3.1-8b-instant", messages=messages)
        trip_plan = response.choices[0].message.content

        destination = extract_destination(trip_plan)
        weather, temp = get_weather(destination)

        accommodations = get_cheapest_accommodation(destination, budget)
        transport_options = get_cheapest_transport(home_city, destination, budget)
        
        st.session_state.preferences = preferences
        st.session_state.mood = mood
        
        return trip_plan, destination, weather, temp, accommodations, transport_options
    except Exception as e:
        st.error(f"Oops! Something went wrong: {e}")
        return None, None, None, None, None, None

# Updated Navigation Bar
def display_nav_bar():
    st.markdown('<div class="navbar">', unsafe_allow_html=True)
    
    st.markdown('<div class="navbar-brand">', unsafe_allow_html=True)
    st.markdown('<span class="logo-text">🌍✨ HIDDEN HORIZONS</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="navbar-menu">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
    
    with col1:
        if st.button("Home", key="nav_home_button"):
            if st.session_state.logged_in:
                go_to_home()
                st.rerun()
            else:
                go_to_login()
                st.rerun()
    
    with col2:
        if st.button("Contact", key="nav_contact_button"):
            go_to_contact()
            st.rerun()
    
    if st.session_state.logged_in:
        with col3:
            if st.button("Logout", key="nav_logout_button"):
                st.session_state.logged_in = False
                st.session_state.user_id = None
                st.session_state.username = "Guest"
                go_to_login()
                st.rerun()
    else:
        with col3:
            if st.button("Login", key="nav_login_button"):
                go_to_login()
                st.rerun()
        
        with col4:
            if st.button("Sign Up", key="nav_signup_button"):
                go_to_signup()
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("<hr>", unsafe_allow_html=True)

# Login Page
def display_login_page():
    display_nav_bar()
    
    st.markdown("<h2>Login to Your Account</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Welcome Back!")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Login", key="login_submit_button"):
                if username and password:
                    success, user_id = login_user(st.session_state.db_conn, username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.user_id = user_id
                        st.session_state.username = username
                        st.session_state.login_error = False
                        go_to_home()
                        st.rerun()
                    else:
                        st.session_state.login_error = True
                        st.error("Invalid username or password!")
                else:
                    st.warning("Please enter both username and password.")
        
        with col_btn2:
            if st.button("Sign Up Instead", key="go_to_signup_button"):
                go_to_signup()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Benefits")
        st.markdown("""
        - Plan personalized getaways
        - Get AI-powered recommendations
        - Secure account management
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Signup Page
def display_signup_page():
    display_nav_bar()
    
    st.markdown("<h2>Create Your Account</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Join Our Community")
        
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm_password")
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("Sign Up", key="signup_submit_button"):
                if username and email and password and confirm_password:
                    if password != confirm_password:
                        st.error("Passwords do not match!")
                    elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                        st.error("Please enter a valid email address.")
                    else:
                        user_exists, _ = check_user_exists(st.session_state.db_conn, username)
                        if user_exists:
                            st.error("Username already exists. Please choose another one.")
                        else:
                            success, user_id = register_user(st.session_state.db_conn, username, email, password)
                            if success:
                                st.session_state.signup_success = True
                                st.success("Account created successfully! Please login.")
                                time.sleep(1)
                                go_to_login()
                                st.rerun()
                            else:
                                st.error("An error occurred during registration. Please try again.")
                else:
                    st.warning("Please fill in all fields.")
        
        with col_btn2:
            if st.button("Login Instead", key="go_to_login_button"):
                go_to_login()
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Why Join Us?")
        st.markdown("""
        - Free personalized travel planning
        - AI-powered destination recommendations
        - Secure and private account
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Contact Page
def display_contact_page():
    display_nav_bar()
    
    st.markdown("<h2>Contact Us</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Get in Touch")
        
        name = st.text_input("Your Name", key="contact_name")
        email = st.text_input("Your Email", key="contact_email")
        message = st.text_area("Your Message", height=150, key="contact_message")
        
        if st.button("Send Message", key="contact_submit_button"):
            if name and email and message:
                st.success("Thank you for your message! We'll get back to you soon.")
                st.session_state.contact_name = ""
                st.session_state.contact_email = ""
                st.session_state.contact_message = ""
            else:
                st.warning("Please fill in all fields.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Our Information")
        st.markdown("""
        *Address:*  
        HIDDEN HORIZONS  
        123 Innovation Lane  
        Tech Valley, CA 94043
        
        *Email:*  
        support@hiddenhorizons.com
        
        *Phone:*  
        +1 (555) 123-4567
        
        *Hours:*  
        Mon-Fri: 9AM - 6PM (PST)  
        Sat-Sun: 10AM - 4PM (PST)
        """)
        st.markdown('</div>', unsafe_allow_html=True)

# Home Page
def display_home_page():
    if not st.session_state.logged_in:
        go_to_login()
        st.rerun()
    
    display_nav_bar()
    
    st.markdown("<h2>Plan Your Perfect Travel Plany</h2>", unsafe_allow_html=True)
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.home_city = st.text_input(
            "Your Current City", 
            value=st.session_state.home_city,
            placeholder="e.g., Mumbai",
            key="home_city_input"
        )
        
        st.session_state.budget = st.number_input(
            "Your Budget (₹)", 
            min_value=1000, 
            max_value=100000, 
            value=st.session_state.budget,
            step=1000,
            key="budget_input"
        )
        
        st.session_state.preferences = st.text_area(
            "Travel Preferences", 
            value=st.session_state.preferences,
            placeholder="I love nature, hiking, local food, historical places...",
            key="preferences_input"
        )
        
        st.session_state.mood = st.text_input(
            "Current Mood", 
            value=st.session_state.mood,
            placeholder="e.g., I need to recharge, excited for adventure...",
            key="mood_input"
        )
    
    with col2:
        st.session_state.trip_length = st.slider(
            "Trip Duration (days)", 
            min_value=1, 
            max_value=7, 
            value=st.session_state.trip_length,
            key="trip_length_slider"
        )
        
        max_travel_time = st.slider(
            "Maximum Travel Time (hours)", 
            min_value=1, 
            max_value=12, 
            value=6,
            key="max_travel_time_slider"
        )
        
        st.session_state.start_date = st.date_input(
            "Start Date", 
            value=st.session_state.start_date,
            min_value=datetime.today().date(),
            key="start_date_input"
        )
        
        transport_mode = st.selectbox(
            "Preferred Transport Mode",
            options=["Any", "Train", "Bus","Bike", "Car", "Flight"],
            index=0,
            key="transport_mode_select"
        )
        
        st.session_state.is_architecture_student = st.checkbox(
            "I am an architecture student (get specialized recommendations)",
            value=st.session_state.is_architecture_student,
            key="arch_student_checkbox"
        )
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
    with col_btn2:
        if st.button("Plan My Getaway", key="plan_trip_button", use_container_width=True):
            if not st.session_state.home_city:
                st.error("Please enter your current city.")
            elif not st.session_state.preferences:
                st.warning("Please share some travel preferences for better recommendations.")
            else:
                with st.spinner("Planning your perfect getaway... 🌍✨"):
                    trip_plan, destination, weather, temp, accommodations, transport_options = plan_getaway(
                        st.session_state.home_city,
                        st.session_state.budget,
                        st.session_state.preferences,
                        st.session_state.mood,
                        st.session_state.trip_length,
                        max_travel_time,
                        st.session_state.start_date,
                        transport_mode,
                        st.session_state.is_architecture_student
                    )
                    
                    if trip_plan:
                        st.session_state.trip_plan = trip_plan
                        st.session_state.destination = destination
                        st.session_state.weather = weather
                        st.session_state.temp = temp
                        st.session_state.accommodations = accommodations
                        st.session_state.transport_options = transport_options
                        go_to_results()
                        st.rerun()
                    else:
                        st.error("Sorry, we couldn't plan your trip at this time. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    

# Results Page
def display_results_page():
    if not st.session_state.trip_plan:
        go_to_home()
        st.rerun()
    
    display_nav_bar()
    
    st.markdown(f"<h2>Your Perfect Getaway to {st.session_state.destination}</h2>", unsafe_allow_html=True)
    
    weather_emoji = "☀"
    if "rain" in st.session_state.weather.lower():
        weather_emoji = "🌧"
    elif "cloud" in st.session_state.weather.lower():
        weather_emoji = "☁"
    elif "snow" in st.session_state.weather.lower():
        weather_emoji = "❄"
    elif "fog" in st.session_state.weather.lower():
        weather_emoji = "🌫"
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Trip Overview")
        
        end_date = st.session_state.start_date + timedelta(days=st.session_state.trip_length)
        date_range = f"{st.session_state.start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}"
        
        st.markdown(f"🗓 When:** {date_range}")
        st.markdown(f"🌡 Weather:** {weather_emoji} {st.session_state.weather} ({st.session_state.temp:.1f}°C)")
        st.markdown(f"💰 Budget:** ₹{st.session_state.budget}")
        st.markdown(f"🎭 Mood:** {st.session_state.mood}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("Quick Actions")
        
        if st.button("Plan Another Trip", key="plan_another_button"):
            go_to_home()
            st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("Your Travel Itinerary")
    st.markdown(st.session_state.trip_plan)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🏨 Recommended Accommodations")
        
        for acc in st.session_state.accommodations:
            st.markdown(f'<div class="accommodation-card">', unsafe_allow_html=True)
            st.markdown(f"{acc['name']}")
            st.markdown(f"Price: {acc['price']}")
            st.markdown(f"[View Details]({acc['link']})")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="css-card">', unsafe_allow_html=True)
        st.subheader("🚆 Transport Options")
        
        for transport in st.session_state.transport_options:
            st.markdown(f'<div class="accommodation-card">', unsafe_allow_html=True)
            st.markdown(f"{transport['mode']}")
            st.markdown(f"Route: {transport['route']}")
            st.markdown(f"Price: {transport['price']}")
            st.markdown(f"[Book Now]({transport['link']})")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="css-card">', unsafe_allow_html=True)
    st.subheader("🌟 AI Travel Tips")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("*What to Pack*")
        if "rain" in st.session_state.weather.lower():
            st.markdown("- Umbrella or rain jacket")
            st.markdown("- Waterproof footwear")
        elif float(st.session_state.temp) > 30:
            st.markdown("- Lightweight clothing")
            st.markdown("- Sunscreen and hat")
        elif float(st.session_state.temp) < 15:
            st.markdown("- Warm jacket and layers")
            st.markdown("- Thermal wear if needed")
        st.markdown("- Comfortable walking shoes")
        st.markdown("- Power bank for devices")
    
    with col2:
        st.markdown("*Local Etiquette*")
        st.markdown("- Dress modestly when visiting religious sites")
        st.markdown("- Learn a few local phrases")
        st.markdown("- Try to use digital payments when possible")
        st.markdown("- Be respectful of local customs")
    
    with col3:
        st.markdown("*Safety Tips*")
        st.markdown("- Keep digital copies of important documents")
        st.markdown("- Share your itinerary with family")
        st.markdown("- Stay hydrated and use sunscreen")
        st.markdown("- Save emergency contact numbers")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("Share on WhatsApp", key="whatsapp_share_button"):
            share_text = f"Check out my weekend getaway to {st.session_state.destination}!"
            st.success("Share feature is demo only.")
    
    with col2:
        if st.button("Download as PDF", key="pdf_download_button"):
            st.success("Download feature is demo only.")

# Main function
def main():
    if st.session_state.page == "login":
        display_login_page()
    elif st.session_state.page == "signup":
        display_signup_page()
    elif st.session_state.page == "home":
        display_home_page()
    elif st.session_state.page == "results":
        display_results_page()
    elif st.session_state.page == "contact":
        display_contact_page()
    else:
        display_login_page()
    
    st.markdown('<div class="footer">', unsafe_allow_html=True)
    st.markdown('© 2025 HIDDEN HORIZONS. All rights reserved.')
    st.markdown('Powered by NULLPOINTERS for better travel experiences.')
    st.markdown('</div>', unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    main()
