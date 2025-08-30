import streamlit as st
import mysql.connector
import uuid
from passlib.context import CryptContext

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

# --- Helpers ---
def create_user(username, email, password):
    token = str(uuid.uuid4())
    hashed = pwd_context.hash(password)
    cur.execute("""
        INSERT INTO users (username, email, password_hash, verification_token, is_verified)
        VALUES (%s, %s, %s, %s, %s)
    """, (username, email, hashed, token, False))
    conn.commit()
    return token

def verify_token(token):
    cur.execute("SELECT username FROM users WHERE verification_token=%s", (token,))
    result = cur.fetchone()
    if result:
        cur.execute("UPDATE users SET is_verified=TRUE, verification_token=NULL WHERE verification_token=%s", (token,))
        conn.commit()
        return True
    return False

def login_user(username, password):
    cur.execute("SELECT password_hash, is_verified FROM users WHERE username=%s", (username,))
    result = cur.fetchone()
    if result:
        hashed_pw, is_verified = result
        if not is_verified:
            return "unverified"
        if pwd_context.verify(password, hashed_pw):
            return "success"
    return "fail"

# --- Streamlit App ---
st.title("Community Sign Up & Login")

page = st.sidebar.selectbox("Page", ["Sign Up", "Verify Email", "Login"])

if page == "Sign Up":
    st.subheader("Create your account")
    username = st.text_input("Username", key="su_username")
    email = st.text_input("Email", key="su_email")
    password = st.text_input("Password", type="password", key="su_password")
    if st.button("Sign Up"):
        token = create_user(username, email, password)
        st.success("Account created! Copy this verification token and go to 'Verify Email' page.")
        st.info(f"Your token: {token}")

elif page == "Verify Email":
    st.subheader("Verify your account")
    token_input = st.text_input("Enter your verification token")
    if st.button("Verify"):
        if verify_token(token_input):
            st.success("Your email is verified! You can now log in.")
        else:
            st.error("Invalid token.")

elif page == "Login":
    st.subheader("Login to your account")
    login_user_input = st.text_input("Username", key="li_username")
    login_pass_input = st.text_input("Password", type="password", key="li_password")
    if st.button("Login"):
        status = login_user(login_user_input, login_pass_input)
        if status == "success":
            st.session_state.logged_in = True
            st.session_state.username = login_user_input
            st.success(f"Welcome {login_user_input}!")
        elif status == "unverified":
            st.error("Please verify your email before logging in.")
        else:
            st.error("Invalid username or password.")
