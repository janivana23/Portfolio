import streamlit as st
import mysql.connector
import bcrypt
import smtplib
import ssl
import random
from datetime import datetime, timedelta

# -------------------- Python File ----------------------------
import Data
import Map
import Analytics
import Download
import Upload

# -------------------- Database Connection --------------------
DB_USER = st.secrets["mysql"]["user"]
DB_PASSWORD = st.secrets["mysql"]["password"]
DB_HOST = st.secrets["mysql"]["host"]
DB_NAME = st.secrets["mysql"]["database"]
DB_PORT = 3306
DB_CA = st.secrets["mysql"]["ca"]


conn = mysql.connector.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME,
    port=DB_PORT,
    ssl_ca=DB_CA
)
cur = conn.cursor(buffered=True)

# -------------------- Email Setup --------------------
SENDER_EMAIL = st.secrets["email"]["address"]
APP_PASSWORD = st.secrets["email"]["app_password"]

def send_token_email(receiver_email, token):
    subject = "Your Verification Token"
    body = f"Your verification token is: {token}"
    message = f"Subject: {subject}\n\n{body}"
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, message)

# -------------------- Helpers --------------------
def create_user(username, email, password):
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cur.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
                (username, email, hashed_pw.decode('utf-8')))
    conn.commit()
    user_id = cur.lastrowid
    return user_id

def generate_token(user_id):
    token = str(random.randint(100000, 999999))  # 6-digit token
    expires_at = datetime.now() + timedelta(minutes=15)
    cur.execute(
        "INSERT INTO verification_tokens (user_id, token, expires_at) VALUES (%s, %s, %s)",
        (user_id, token, expires_at)
    )
    conn.commit()
    return token

def verify_token_db(user_id, token_input):
    cur.execute(
        "SELECT token, expires_at, used FROM verification_tokens WHERE user_id=%s AND used=0 ORDER BY created_at DESC LIMIT 1",
        (user_id,)
    )
    result = cur.fetchone()
    if result:
        token, expires_at, used = result
        if datetime.now() > expires_at:
            return "expired"
        elif token_input == token:
            cur.execute("UPDATE users SET is_verified=1 WHERE id=%s", (user_id,))
            cur.execute("UPDATE verification_tokens SET used=1 WHERE user_id=%s AND token=%s", (user_id, token))
            conn.commit()
            return "verified"
    return "invalid"

def login_user(username, password):
    cur.execute("SELECT id, password_hash, is_verified FROM users WHERE username=%s", (username,))
    result = cur.fetchone()
    if result:
        user_id, hashed_pw, is_verified = result
        if not is_verified:
            return "unverified"
        elif bcrypt.checkpw(password.encode('utf-8'), hashed_pw.encode('utf-8')):
            return "success"
        else:
            return "wrong"
    else:
        return "notfound"

# -------------------- Streamlit App --------------------
st.title("Community Sign Up & Login")

page = st.sidebar.selectbox("Page", ["Sign Up", "Verify Email", "Login", "Data", "Map", "Analytics", "Download", "Upload"])

if page == "Sign Up":
    st.subheader("Create your account")
    username = st.text_input("Username", key="su_user")
    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_pass")
    if st.button("Sign Up"):
        if username and email and password:
            cur.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
            if cur.fetchone():
                st.error("Username or Email already exists.")
            else:
                user_id = create_user(username, email, password)
                token = generate_token(user_id)
                send_token_email(email, token)
                st.success(f"Account created! Verification token sent to {email}.")
        else:
            st.error("Please fill in all fields.")

elif page == "Verify Email":
    st.subheader("Verify your email")
    username = st.text_input("Username for verification", key="v_user")
    token_input = st.text_input("Enter verification token", key="v_token")
    if st.button("Verify"):
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
        if user:
            user_id = user[0]
            status = verify_token_db(user_id, token_input)
            if status == "verified":
                st.success("Email verified! You can now log in.")
            elif status == "expired":
                st.error("Token expired. Please sign up again.")
            else:
                st.error("Invalid token.")
        else:
            st.error("Username not found.")

elif page == "Login":
    st.subheader("Login")
    username = st.text_input("Username", key="li_user")
    password = st.text_input("Password", type="password", key="li_pass")
    if st.button("Login"):
        status = login_user(username, password)
        if status == "success":
            st.session_state.logged_in = True
            st.session_state.username = username
            st.success(f"Welcome {username}!")
            conn = mysql.connector.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                database=DB_NAME,
                port=DB_PORT
            )
            st.session_state.conn = conn
            st.session_state.connected = True
            st.success("✅ Connected to MySQL Database!")
        elif status == "unverified":
            st.error("Please verify your email first.")
        elif status == "wrong":
            st.error("Incorrect password.")
        else:
            st.error("User not found.")

elif page == "Data":
    Data.app()  # function inside data.py
elif page == "Analytics":
    Analytics.app()
elif page == "Map":
    Map.app()
elif page == "Upload":
    if st.session_state.logged_in:
        Upload.app()
    else: 
        st.write ("Please login before you can upload into the database")
elif page == "Download":
    Download.app()
