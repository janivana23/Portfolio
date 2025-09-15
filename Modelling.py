import streamlit as st
import pandas as pd
import mysql.connector
from sklearn.ensemble import GradientBoostingRegressor
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
        cols = [col[0] for col in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.lower()
        for col, dtype in listdtype:
            if dtype in ["float", "int"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    # -------------------- Load Data --------------------
    query = "SELECT * FROM TRAIN_VOLUME;"
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int")]
    df = run_query(query, listdtype)
    
    st.title("🚇 Singapore Train Station Modelling Analytics")

    # -------------------- Preprocess --------------------
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])
    df["day_of_week"] = df["train_volume_year_month"].dt.dayofweek  # 0=Mon,6=Sun
    df["train_volume_day"] = df["train_volume_day"].map({"WEEKDAY": 0, "WEEKENDS/HOLIDAY": 1})
    
    # Drop rows with missing values in important columns
    df = df.dropna(subset=["train_volume_tap_in", "train_volume_day", "train_code"])

    # One-hot encode train_code
    df = pd.get_dummies(df, columns=["train_code"], drop_first=True)

    # Split train/test by month
    months = df["train_volume_year_month"].dt.to_period("M").unique()
    if len(months) < 2:
        st.error("❌ Not enough months of data to split into train/test")
        return

    train_month = months[-2]
    test_month = months[-1]

    train = df[df["train_volume_year_month"].dt.to_period("M") == train_month]
    test = df[df["train_volume_year_month"].dt.to_period("M") == test_month]

    # -------------------- Features/Target --------------------
    feature_cols = [c for c in train.columns if c not in ["train_volume_tap_in", "train_volume_tap_out", "train_volume_year_month"]]
    X_train = train[feature_cols]
    y_train = train["train_volume_tap_in"]
    X_test = test[feature_cols]
    y_test = test["train_volume_tap_in"]

    # -------------------- Model --------------------
    model = GradientBoostingRegressor(n_estimators=500, learning_rate=0.05, max_depth=3, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # -------------------- Metrics --------------------
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    st.write(f"MSE: {mse:.2f}")
    st.write(f"MAE: {mae:.2f}")
    st.write(f"R²: {r2:.2f}")

    # -------------------- Visualization --------------------
    plt.figure(figsize=(12,5))
    plt.plot(test["train_volume_year_month"], y_test, label="Actual", marker='o')
    plt.plot(test["train_volume_year_month"], y_pred, label="Predicted", marker='x')
    plt.xlabel("Date")
    plt.ylabel("Tap-In Volume")
    plt.title("Actual vs Predicted Tap-In Volume")
    plt.legend()
    st.pyplot(plt)
