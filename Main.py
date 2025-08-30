import streamlit as st
import mysql.connector
import bcrypt
import uuid

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

# --- Check if URL contains token (verification) ---
token = st.experimental_get_query_params().get("token", [None])[0]
if token:
    cur.execute("UPDATE users SET is_verified=TRUE WHERE verification_token=%s", (token,))
    conn.commit()
    st.success("✅ Your account has been verified! You can now log in.")

st.title("🚇 MRT App: Signup & Login")

# --- Signup Section ---
st.subheader("Sign Up")
signup_username = st.text_input("Username", key="signup_username")
signup_email = st.text_input("Email", key="signup_email")
signup_password = st.text_input("Password", type="password", key="signup_password")

if st.button("Sign Up"):
    if signup_username and signup_email and signup_password:
        # Check if username or email exists
        cur.execute("SELECT * FROM users WHERE username=%s OR email=%s", (signup_username, signup_email))
        if cur.fetchone():
            st.error("❌ Username or email already exists.")
        else:
            hashed = bcrypt.hashpw(signup_password.encode('utf-8'), bcrypt.gensalt())
            verification_token = str(uuid.uuid4())
            cur.execute("""
                INSERT INTO users (username, email, password_hash, verification_token)
                VALUES (%s, %s, %s, %s)
            """, (signup_username, signup_email, hashed, verification_token))
            conn.commit()
            # Display verification link in app
            verification_link = f"{st.get_url()}?token={verification_token}"
            st.success("✅ Account created!")
            st.info(f"Click the link below to verify your account:\n\n[{verification_link}]({verification_link})")
    else:
        st.warning("⚠️ Please fill in all signup fields.")

# --- Login Section ---
st.subheader("Login")
login_user = st.text_input("Username", key="login_user")
login_pass = st.text_input("Password", type="password", key="login_pass")

if st.button("Login"):
    if login_user and login_pass:
        cur.execute("SELECT password_hash, is_verified FROM users WHERE username=%s", (login_user,))
        result = cur.fetchone()
        if not result:
            st.error("❌ Username does not exist.")
        else:
            hashed_pw, is_verified = result
            if not is_verified:
                st.warning("⚠️ Please verify your account first.")
            elif bcrypt.checkpw(login_pass.encode('utf-8'), hashed_pw.encode('utf-8')):
                st.session_state.logged_in = True
                st.session_state.username = login_user
                st.success(f"✅ Welcome {login_user}!")
            else:
                st.error("❌ Incorrect password.")
    else:
        st.warning("⚠️ Please fill in all login fields.")
