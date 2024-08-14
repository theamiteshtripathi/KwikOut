import streamlit as st
import mysql.connector
import googlemaps
import time
from dotenv import load_dotenv
import urllib.parse
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
    /* Styling for visible destination input */
    .destination-input {
        margin-top: 20px;
        color: #000000; /* Ensure text is visible */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Create two empty columns and place the logo in the middle one
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("kwikout.png", caption="KwikOut", width=150)


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

# Function to add user to exit queue and reset status
def add_to_queue(user_id, zone):
    conn = create_connection()
    cursor = conn.cursor()

    # Reset the user's status to 'waiting' when they join the queue
    cursor.execute("UPDATE exit_queue SET status = 'waiting' WHERE user_id = %s", (user_id,))
    
    # Only consider users who are still waiting for the max queue number
    cursor.execute("SELECT MAX(queue_number) FROM exit_queue WHERE zone = %s AND status = 'waiting'", (zone,))
    max_queue_number = cursor.fetchone()[0]
    next_queue_number = (max_queue_number or 0) + 1
    
    # Insert the user into the queue with 'waiting' status
    cursor.execute("INSERT INTO exit_queue (user_id, queue_number, zone, status) VALUES (%s, %s, %s, 'waiting')", (user_id, next_queue_number, zone))
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

# Function to update user's status to 'exited'
def update_user_status(user_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE exit_queue SET status = 'exited' WHERE user_id = %s", (user_id,))
    conn.commit()
    conn.close()

def get_navigation_link(destination):
    try:
        if not destination:
            st.error("Destination cannot be empty.")
            return None

        # Get geocode result for the destination
        geocode_result = gmaps.geocode(destination)
        
        if not geocode_result:
            st.error("Location not found. Please check the destination input.")
            return None
        
        # Extract latitude and longitude from the geocode result
        location = geocode_result[0]['geometry']['location']
        latitude = location['lat']
        longitude = location['lng']
        
        # Log latitude and longitude for debugging
        st.write(f"Latitude: {latitude}, Longitude: {longitude}")
        
        # Define a proper origin, e.g., a specific address or coordinates
        origin = "360 Huntington Ave, Boston, MA"  # Example: Northeastern University
        
        # URL encode the origin and destination
        origin_encoded = urllib.parse.quote(origin)
        destination_encoded = f"{latitude},{longitude}"
        
        # Generate the Google Maps URL with the origin and latitude,longitude destination
        google_maps_url = f"https://www.google.com/maps/dir/?api=1&origin={origin_encoded}&destination={destination_encoded}&travelmode=driving"
        
        # Display the navigation link
        st.markdown(f"[Click here for navigation]({google_maps_url})")
        
        return google_maps_url
        
    except googlemaps.exceptions.ApiError as e:
        st.error(f"Google Maps API Error: {e}")
        return None
    except googlemaps.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {e}")
        return None

# Sample data for restaurants (You can replace this with your actual data)
restaurants = [
    {"name": "Neptune Oyster", "image": "assets/restraunt1.jpeg", "discount": "10% OFF"},
    {"name": "Union Oyster House", "image": "assets/restraunt2.jpeg", "discount": "15% OFF"},
    {"name": "The Capital Grille", "image": "assets/restraunt3.jpeg", "discount": "Buy 1 Get 1 Free"},
    {"name": "Lolita Cocina & Tequila Bar", "image": "assets/restraunt4.jpeg", "discount": "20% OFF"},
    {"name": "Yvonne's", "image": "assets/restraunt5.jpeg", "discount": "Free Dessert with Meal"},
    {"name": "Toro", "image": "assets/restraunt6.jpeg", "discount": "25% OFF"},
    {"name": "Carmelina's", "image": "assets/restraunt7.jpeg", "discount": "30% OFF"},
    {"name": "Mamma Maria", "image": "assets/restraunt8.jpeg", "discount": "40% OFF"},
    {"name": "Ostra", "image": "assets/restraunt9.jpeg", "discount": "50% OFF"},
    # Add more restaurants as needed
]

# Function to display the explore page with dynamic restaurant boxes and enhanced text visibility
def explore_page():
    st.title("Explore Restaurants and Coupons")

    # Loop through the restaurants and display them in a 3-column layout
    cols = st.columns(3)
    for index, restaurant in enumerate(restaurants):
        with cols[index % 3]:  # Distribute restaurants across three columns
            st.image(restaurant['image'], width=200)
            st.markdown(f"<h3 style='color: black;'>{restaurant['name']}</h3>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: black;'>{restaurant['discount']}</p>", unsafe_allow_html=True)



# Page Navigation
page = st.sidebar.selectbox("Navigate", ["Login", "Sign Up", "Queue Management", "Explore"])

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
            st.session_state.leave_requested = False  # Initialize leave request flag
            st.session_state.status = None  # Reset status on new login
        else:
            st.error("Invalid username or password")

elif page == "Sign Up":
    st.markdown('<div class="header">Sign Up</div>', unsafe_allow_html=True)
    username = st.text_input("Username", placeholder="Enter your username")
    password = st.text_input("Password", type='password', placeholder="Enter your password")
    if st.button("Sign Up"):
        create_user(username, password)
        st.success("User created successfully!")

elif page == "Explore":
    explore_page()

# Queue Management Page
if st.session_state.get("authenticated", False) and st.session_state.page == "Queue Management":
    st.markdown('<div class="header">Queue Management</div>', unsafe_allow_html=True)
    
    if not st.session_state.get("leave_requested", False):
        zone = st.selectbox("Select your zone", ["A", "B", "C"])
        if st.button("I want to leave"):
            queue_number = add_to_queue(st.session_state.user_id, zone)
            st.success(f"You are in queue. Your number is {queue_number}")
            st.session_state.leave_requested = True  # Mark leave request as made
    else:
        st.warning("You have already requested to leave. Please wait for your turn.")

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
                    break
            
            # Ask for destination
            st.markdown('<div class="destination-input">Enter your destination:</div>', unsafe_allow_html=True)
            destination = st.text_input("Enter your destination", key="destination_input")
            if st.button("Get Navigation"):
                navigation_link = get_navigation_link(destination)
                if navigation_link:
                    st.write(f"Navigation Link: {navigation_link}")
                    update_user_status(st.session_state.user_id)  # Update user status to 'exited' after navigation link is generated

    if st.button("Log Out"):
        st.session_state.authenticated = False
        st.session_state.page = "Login"
        st.session_state.leave_requested = False  # Reset leave request flag on logout
        st.session_state.status = None  # Reset status on logout
