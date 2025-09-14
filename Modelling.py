import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector


def app():
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
    
    @st.cache_data
    def run_query(query, listdtype):
        cur = conn.cursor()
        cur.execute(query)
        cols = [col[0] for col in cur.description]  # column names
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.lower()
        # Ensure coordinates are float
        for col, dtype in listdtype:
            if dtype == "float" or dtype == "int":
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")

        return df
    

    #-----------------------------------------------------------------------------------------
    query = "SELECT * FROM TRAIN_VOLUME;"  # adjust columns as needed
    df = pd.read_sql(query, conn)
    conn.close()

    print(df.head())
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int")]
    df = run_query(query, listdtype)

    st.title("🚇 Singapore Train Station Modelling Analytics")