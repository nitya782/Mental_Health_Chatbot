import streamlit as st
import json
import os
import hashlib

st.set_page_config(page_title="Authentication", layout="centered")

st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}  /* Hide Sidebar */
    </style>
    """, unsafe_allow_html=True)

USER_DB = "users.json"

# Load user credential
def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                return {}  # Return empty dict if file is corrupted
    return {}

# Save new users
def save_users(users):
    with open(USER_DB, "w") as file:
        json.dump(users, file, indent=4)

# Hash password for security
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Authenticate user
def authenticate(username, password):
    users = load_users()
    hashed_password = hash_password(password)

    if username in users:
        stored_password = users[username]
        if stored_password == password or stored_password == hashed_password:
            return True
    return False

# Register a new user
def register_user(username, password):
    users = load_users()
    if username in users:
        return False  # Username already exists
    users[username] = hash_password(password)  # Store hashed password
    save_users(users)
    return True

# Initialize session state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

tab1, tab2 = st.tabs(["Login", "Sign Up"])

# 🔹 Login Tab
with tab1:
    st.markdown("##  Login")
    login_username = st.text_input("Username", key="login_user")
    login_password = st.text_input("Password", type="password", key="login_pass")

    if st.button("Login"):
        print(f"Trying to login: {login_username}")
    if authenticate(login_username, login_password):
        st.session_state["authenticated"] = True
        st.session_state["username"] = login_username
        st.success("✅ Login successful! Redirecting...")
        print("Login successful!")
        st.switch_page("pages/frontend.py")  # Redirect to your chatbot page
    else:
        print("Login failed!")


# 🔹 Sign-up Tab
with tab2:
    st.markdown("## Create an Account")
    signup_username = st.text_input("Choose a Username", key="signup_user")
    signup_password = st.text_input("Choose a Password", type="password", key="signup_pass")
    confirm_password = st.text_input("Confirm Password", type="password", key="confirm_pass")

    if st.button("Sign Up"):
        if signup_password != confirm_password:
            st.error("❌ Passwords do not match!")
        elif register_user(signup_username, signup_password):
            st.success("✅ Account created! Please log in.")
        else:
            st.warning("⚠️ Username already exists! Try logging in.")
