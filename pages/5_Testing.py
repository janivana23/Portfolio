import mysql.connector
import streamlit as st

conn = mysql.connector.connect(
    host=st.secrets["mysql"]["host"],
    user=st.secrets["mysql"]["user"],
    password=st.secrets["mysql"]["password"],
    database=st.secrets["mysql"]["database"],
)

st.success("✅ Connected successfully with secrets.toml")
