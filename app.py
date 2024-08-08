import streamlit as st
import mysql.connector
import googlemaps
from datetime import datetime, timedelta

# Set the Streamlit page configuration
st.set_page_config(page_title="KwikOut", page_icon="🚗")
st.markdown("<style>footer {visibility: hidden;}</style>", unsafe_allow_html=True)
st.markdown("<style>header {visibility: hidden;}</style>", unsafe_allow_html=True)

st.image("kwikout.png", width=100)


# Set up MySQL connection
def create_connection():
    return mysql.connector.connect(
        host='localhost',
        user='amitesh',  # replace with your MySQL username
        password='12345',  # replace with your MySQL password
        database='exit_management'
    )

# Google Maps API setup
gmaps = googlemaps.Client(key='AIzaSyDsHL9QdwdUgP49AOEudOkQew0DFeXpNWI')

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

# Streamlit UI
st.title("🏁KwikOut: Exit Management System🏎️")

# Signup/Login Form
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    username = st.text_input("Username")
    password = st.text_input("Password", type='password')
    if st.button("Sign Up"):
        create_user(username, password)
        st.success("User created successfully!")

    if st.button("Log In"):
        user = authenticate_user(username, password)
        if user:
            st.success("Logged in successfully!")
            st.session_state.authenticated = True
            st.session_state.user_id = user[0]
        else:
            st.error("Invalid username or password")
else:
    # Exit Queue
    zone = st.selectbox("Select your zone", ["A", "B", "C"])
    if st.button("I want to leave"):
        queue_number = add_to_queue(st.session_state.user_id, zone)
        st.success(f"You are in queue. Your number is {queue_number}")

    queue_status = get_queue_status(st.session_state.user_id)
    if queue_status:
        st.write(f"Your queue number: {queue_status[0]}")
        st.write(f"Your zone: {queue_status[1]}")
        st.write(f"Your status: {queue_status[2]}")

        # Check if user can leave
        if queue_status[2] == 'waiting' and queue_status[0] == 1:
            st.success("You can exit now!")
            # Update status to exited
            conn = create_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE exit_queue SET status = 'exited' WHERE user_id = %s", (st.session_state.user_id,))
            conn.commit()
            conn.close()

            destination = st.text_input("Enter your destination")
            if st.button("Get Navigation"):
                navigation_link = get_navigation_link(destination)
                st.write(f"Navigation Link: {navigation_link}")

        else:
            st.warning("Please wait for your turn")

    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.user_id = None

