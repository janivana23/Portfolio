import streamlit as st
import pandas as pd

import mysql.connector

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

import matplotlib.pyplot as plt

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
    query = "SELECT * FROM TRAIN_VOLUME;" 
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int")]
    df = run_query(query, listdtype)

    st.title("🚇 Singapore Train Station Modelling Analytics")

    # Make sure that year month is datetime
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])
    # Encode day type (Weekday/Weekend)
    df["train_volume_day"] = df["train_volume_day"].map({"WEEKDAY": 0, "WEEKENDS/HOLIDAY": 1})

    #Split data to train and test
    # Convert to "period month" so year+month are grouped properly
    months = df["train_volume_year_month"].dt.to_period("M").unique()

    if len(months) >= 2:
        train_month = months[-2]  # second last month
        test_month  = months[-1]  # last month

        train = df[df["train_volume_year_month"].dt.to_period("M") == train_month]
        test  = df[df["train_volume_year_month"].dt.to_period("M") == test_month]
    else:
        st.error("❌ Not enough months of data to split into train/test")
        train, test = pd.DataFrame(), pd.DataFrame()

    # Create x and y train test
    y_train = train["train_volume_tap_in"]
    y_test  = test["train_volume_tap_in"]

    X_train = train[["train_volume_day"]]
    X_test  = test[["train_volume_day"]]

    train_clean = train.dropna(subset=["train_volume_day", "train_volume_tap_in"])
    X_train = train_clean[["train_volume_day"]]
    y_train = train_clean["train_volume_tap_in"]

    # Regression Model
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    st.write("MSE:", mean_squared_error(y_test, y_pred))
    st.write("MAE:", mean_absolute_error(y_test, y_pred))
    st.write("R²:", r2_score(y_test, y_pred))

    # Visualisation
    plt.figure(figsize=(12,6))
    plt.plot(train_clean["train_volume_year_month"], y_train, label="Train", marker='o')
    plt.plot(test["train_volume_year_month"], y_test, label="Actual Test", marker='o', color="black")
    plt.plot(test["train_volume_year_month"], y_pred, label="Predicted Test", marker='x', color="red")
    plt.xlabel("Date")
    plt.ylabel("Tap-In Volume")
    plt.title("Train Tap-In Volume Prediction")
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(plt)