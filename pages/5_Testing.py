import mysql.connector
import streamlit as st

if "connected" not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    with st.form("db_form"):
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        host = st.text_input("Host", value="yourserver.mysql.database.azure.com")
        submit = st.form_submit_button("Connect")

    if submit:
        try:
            conn = mysql.connector.connect(
                user=user,
                password=password,
                host=host,
                database="singapore_mrt_db"
            )
            st.session_state.conn = conn
            st.session_state.connected = True
            st.success("✅ Connected to MySQL Database!")
        except mysql.connector.Error as e:
            st.error(f"Database connection failed: {e}")
            print(f"MySQL connection error: {e}")  # useful for debugging
            st.stop()

# Optional: show connection status
if st.session_state.connected:
    st.write("Connected! You can now run queries.")