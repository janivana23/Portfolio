import streamlit as st
import mysql.connector
import uuid
from passlib.context import CryptContext
import smtplib
import ssl
import random

# --- Password hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Database connection using Streamlit secrets ---
DB_USER = st.secrets["mysql"]["user"]
DB_PASSWORD = st.secrets["mysql"]["password"]
DB_HOST = st.secrets["mysql"]["host"]
DB_NAME = st.secrets["mysql"]["database"]
DB_PORT = 3306

conn = mysql.connector.connect(
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    database=DB_NAME,
    port=DB_PORT
)
cur = conn.cursor()

st.header("Sign Up or Sign In to access the Database")

# --- Helpers ---
def create_user(username, password, email):
    st.subheader("Create your account")
    cur.execute(f"CREATE USER '{username}'@'%' IDENTIFIED BY '{password}';")
    # Streamlit UI
    if st.button("Send Verification Token"):
        if email:
            token = random.randint(100000, 999999)  # 6-digit token
            send_token_email(email, token)
            st.success(f"Verification token sent to {email}!")
        else:
            st.error("Please enter a valid email.")
    conn.commit()
    return token

# --- Email Function ---
# Email config (store safely in st.secrets in production!)
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

def verify_token(token):
    st.subheader("Verify your account")
    username = st.text_input("Username", key="su_username")
    password = st.text_input("Password", type="password", key="su_password")
    email = st.text_input("Enter your email")
    token = create_user(username, password, email)
    token_input = st.text_input("Enter your verification token")
    if st.button("Verify"):
        if token_input == token:
            token = True
            st.success("Your email is verified! You can now log in.")
            return token
        else:
            st.error("Invalid token.")

def login_user(host):
    if not st.session_state.connected:
        with st.form("db_form"):
            user = st.text_input("Username")
            password = st.text_input("Password", type="password")
            port=3306
            submit = st.form_submit_button("Connect")

        if submit:
            try:
                conn = mysql.connector.connect(
                    user=user,
                    password=password,
                    host=host,
                    port=port,
                    database="singapore_mrt_db"
                )
                st.session_state.conn = conn
                st.session_state.connected = True
                st.success("✅ Connected to MySQL Database!")
            except mysql.connector.Error as e:
                st.error(f"Database connection failed: {e}")
                print(f"MySQL connection error: {e}")  # useful for debugging
                st.stop()
    if st.session_state.connected:
        conn = st.session_state.conn
        cur = conn.cursor()
        cur.execute(f"GRANT ALL PRIVILEGES ON singapore_mrt_db.* TO '{user}'@'%';")
        conn.commit()


# --- Streamlit App ---
st.title("Community Sign Up & Login")

page = st.sidebar.selectbox("Page", ["Sign Up", "Login"])

if page == "Sign Up":
    token = verify_token(token=None)
    if token:
        st.success("You can now log in using your credentials.")
        login_user(host=DB_HOST)

elif page == "Login":
    login_user(host=DB_HOST)
