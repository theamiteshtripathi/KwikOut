import streamlit as st
import mysql.connector
import googlemaps
import time
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Set the Streamlit page configuration
st.set_page_config(page_title="KwikOut", page_icon="🚗", layout="wide")

# Custom CSS for visual enhancement and centering the logo
st.markdown(
    """
    <style>
    /* Overall background color */
    body {
        background-color: #f0f2f6; /* Light grey background */
    }
    /* Main content background and text colors */
    .main {
        background-color: #f8f9fa; /* Light background for contrast */
        color: #000000; /* Black text color */
        border-radius: 10px;
        padding: 20px;
    }
    /* Title and headers */
    .title {
        color: #001f3f; /* Navy blue for title */
        text-align: center;
        font-weight: bold;
        font-size: 36px;
        margin-bottom: 10px;
    }
    .header {
        color: #001f3f; /* Navy blue for headers */
        font-weight: bold;
        font-size: 24px;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    /* Buttons */
    .stButton>button {
        background-color: #001f3f; /* Navy blue button background */
        color: #ffffff; /* White text color */
        border-radius: 5px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #004080; /* Darker navy blue on hover */
        color: #ffffff;
    }
    /* Success and error messages */
    .stAlert {
        background-color: #004080 !important; /* Navy blue background for alerts */
        color: #ffffff !important; /* White text for readability */
    }
    /* Centered logo */
    .center {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    /* Logo styling */
    .center img {
        max-width: 100%;
        width: 150px; /* Adjust logo size */
        height: auto;
    }
    /* Footer */
    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Display the KwikOut logo centered
st.markdown(
    """
    <div class="center">
        <img src="KwikOut.png" alt="KwikOut Logo">
    </div>
    """,
    unsafe_allow_html=True
)

# Title and description
st.markdown('<div class="title">🏁KwikOut: Exit Management System🏎️</div>', unsafe_allow_html=True)

# Set up MySQL connection using environment variables
def create_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

# Google Maps API setup using environment variable
gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))

# Function to create a new user
def create_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
    conn.commit()
    conn.close()

# Function to authenticate user
def authenticate_user(username, password):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
    user = cursor.fetchone()
    conn.close()
    return user

# Function to add user to exit queue
def add_to_queue(user_id, zone):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(queue_number) FROM exit_queue WHERE zone = %s", (zone,))
    max_queue_number = cursor.fetchone()[0]
    next_queue_number = (max_queue_number or 0) + 1
    cursor.execute("INSERT INTO exit_queue (user_id, queue_number, zone) VALUES (%s, %s, %s)", (user_id, next_queue_number, zone))
    conn.commit()
    conn.close()
    return next_queue_number

# Function to get user's queue status
def get_queue_status(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT queue_number, zone, status FROM exit_queue WHERE user_id = %s", (user_id,))
    queue_status = cursor.fetchone()
    conn.close()
    return queue_status

# Function to get the navigation link
def get_navigation_link(destination):
    directions = gmaps.directions("Current Location", destination)
    return directions[0]['overview_polyline']['points']

# Page Navigation
page = st.sidebar.selectbox("Navigate", ["Login", "Sign Up"])

if page == "Login":
    st.markdown('<div class="header">Log In</div>', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type='password', placeholder="Enter your password")
    if st.button("Log In"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in successfully!")
            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
            st.session_state.page = "Queue Management"  # Redirect to Queue Management
        else:
            st.error("Invalid username or password")

elif page == "Sign Up":
    st.markdown('<div class="header">Sign Up</div>', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type='password', placeholder="Enter your password")
    if st.button("Sign Up"):
        create_user(username, password)
        st.success("User created successfully!")

# Queue Management Page
if st.session_state.get("authenticated", False) and st.session_state.page == "Queue Management":
    st.markdown('<div class="header">Queue Management</div>', unsafe_allow_html=True)
    zone = st.selectbox("Select your zone", ["A", "B", "C"])
    if st.button("I want to leave"):
        queue_number = add_to_queue(st.session_state.user_id, zone)
        st.success(f"You are in queue. Your number is {queue_number}")

    queue_status = get_queue_status(st.session_state.user_id)
    if queue_status:
        queue_number = queue_status[0]
        st.write(f"Your queue number: {queue_number}")
        st.write(f"Your zone: {queue_status[1]}")
        st.write(f"Your status: {queue_status[2]}")

        # Auto-decrement queue number every 10 seconds
        if queue_status[2] == 'waiting':
            placeholder = st.empty()
            while queue_number > 1:
                time.sleep(10)  # Simulate time passing
                queue_number -= 1
                with placeholder.container():
                    st.write(f"Queue number updated: {queue_number}")
                if queue_number == 1:
                    st.success("It's your turn to leave!")
                    destination = st.text_input("Enter your destination")
                    if st.button("Get Navigation"):
                        navigation_link = get_navigation_link(destination)
                        st.write(f"Navigation Link: {navigation_link}")
                    break

    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.page = "Login"
