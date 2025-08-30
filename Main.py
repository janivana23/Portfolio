import streamlit as st
import mysql.connector
import smtplib
import ssl
import random

# --- Database connection ---
DB_USER = st.secrets["mysql"]["user"]
DB_PASSWORD = st.secrets["mysql"]["password"]
DB_HOST = st.secrets["mysql"]["host"]
DB_NAME = st.secrets["mysql"]["database"]

conn = mysql.connector.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME,
    port=3306
)
cur = conn.cursor()

# --- Email Config ---
SENDER_EMAIL = st.secrets["email"]["address"]
APP_PASSWORD = st.secrets["email"]["app_password"]

def send_token_email(receiver_email, token):
    subject = "Your Verification Token"
    body = f"Here is your verification token: {token}"
    message = f"Subject: {subject}\n\n{body}"

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, message)

# --- Create user (insert into DB) ---
def create_user(username, password, email):
    token = str(random.randint(100000, 999999))  # 6-digit token
    cur.execute(
        "INSERT INTO users (username, password, email, is_verified, token) VALUES (%s, %s, %s, %s, %s)",
        (username, password, email, False, token)
    )
    conn.commit()
    send_token_email(email, token)
    return token

# --- Verify token ---
def verify_user(username, token_input):
    cur.execute("SELECT token FROM users WHERE username=%s", (username,))
    result = cur.fetchone()
    if result and result[0] == token_input:
        cur.execute("UPDATE users SET is_verified=%s WHERE username=%s", (True, username))
        conn.commit()
        return True
    return False

# --- Login ---
def login_user(username, password):
    cur.execute("SELECT password, is_verified FROM users WHERE username=%s", (username,))
    result = cur.fetchone()
    if result:
        stored_pw, is_verified = result
        if not is_verified:
            st.error("Please verify your email before logging in.")
            return False
        elif password == stored_pw:  # TODO: hash + bcrypt in production
            st.session_state.logged_in = True
            st.session_state.username = username
            return True
    return False

# --- Streamlit App ---
st.title("Community Sign Up & Login")

page = st.sidebar.selectbox("Page", ["Sign Up", "Verify", "Login"])

if page == "Sign Up":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")
    if st.button("Sign Up"):
        token = create_user(username, password, email)
        st.info(f"A verification token was sent to {email}. Please check your inbox.")

elif page == "Verify":
    username = st.text_input("Username")
    token_input = st.text_input("Verification Token")
    if st.button("Verify"):
        if verify_user(username, token_input):
            st.success("Your account is verified! You can now log in.")
        else:
            st.error("Invalid token.")

elif page == "Login":
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user(username, password):
            st.success(f"Welcome {username}!")
        else:
            st.error("Login failed.")
