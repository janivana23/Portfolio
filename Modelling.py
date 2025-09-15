import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
import matplotlib.pyplot as plt

def app():
    st.title("🚇 Singapore Train Station Modelling Analytics - Regression Forecast")

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
        cols = [col[0] for col in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.lower()
        for col, dtype in listdtype:
            if dtype == "float" or dtype == "int":
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    # -------------------- Load Data --------------------
    query = "SELECT * FROM TRAIN_VOLUME;"
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int")]
    df = run_query(query, listdtype)

    # Encode day type
    df["train_volume_day"] = df["train_volume_day"].map({"WEEKDAY": 0, "WEEKENDS/HOLIDAY": 1})
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])
    
    # Drop missing values
    df = df.dropna(subset=["train_volume_day", "train_volume_hour", "train_code", "train_volume_tap_in"])

    # -------------------- Feature Engineering --------------------
    # One-hot encode train_code (station)
    encoder = OneHotEncoder(sparse=False, handle_unknown='ignore')
    train_code_encoded = encoder.fit_transform(df[["train_code"]])
    train_code_cols = [f"station_{c}" for c in encoder.categories_[0]]
    df_encoded = pd.concat([df.reset_index(drop=True), pd.DataFrame(train_code_encoded, columns=train_code_cols)], axis=1)
    
    # Lag features
    df_encoded = df_encoded.sort_values(["train_code", "train_volume_year_month", "train_volume_hour"])
    df_encoded["lag_1"] = df_encoded.groupby("train_code")["train_volume_tap_in"].shift(1)
    df_encoded["lag_2"] = df_encoded.groupby("train_code")["train_volume_tap_in"].shift(2)
    
    # Rolling mean features
    df_encoded["rolling_3"] = df_encoded.groupby("train_code")["train_volume_tap_in"].shift(1).rolling(window=3).mean()
    
    df_encoded = df_encoded.dropna(subset=["lag_1", "lag_2", "rolling_3"])

    # -------------------- Train/Test Split --------------------
    months = df_encoded["train_volume_year_month"].dt.to_period("M").unique()
    if len(months) < 2:
        st.error("❌ Not enough months of data to split")
        return
    
    train_month = months[-2]
    test_month  = months[-1]
    
    train = df_encoded[df_encoded["train_volume_year_month"].dt.to_period("M") == train_month]
    test  = df_encoded[df_encoded["train_volume_year_month"].dt.to_period("M") == test_month]

    feature_cols = ["train_volume_day", "train_volume_hour", "lag_1", "lag_2", "rolling_3"] + train_code_cols
    X_train = train[feature_cols]
    y_train = train["train_volume_tap_in"]
    X_test  = test[feature_cols]
    y_test  = test["train_volume_tap_in"]

    # -------------------- Regression --------------------
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # -------------------- Metrics --------------------
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    st.write(f"MSE: {mse:.2f}")
    st.write(f"MAE: {mae:.2f}")
    st.write(f"R²: {r2:.2f}")

    # -------------------- Visualization --------------------
    plt.figure(figsize=(12,6))
    plt.plot(test["train_volume_year_month"], y_test, label="Actual", marker='o')
    plt.plot(test["train_volume_year_month"], y_pred, label="Predicted", marker='x')
    plt.xlabel("Date")
    plt.ylabel("Tap-in Volume")
    plt.title("Train Station Tap-in Forecast")
    plt.legend()
    st.pyplot(plt)

