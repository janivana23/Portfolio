import streamlit as st
import pandas as pd
import numpy as np
import mysql.connector
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import matplotlib.pyplot as plt

def app():
    st.title("🚇 Singapore Train Station Regression Analytics")

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
        # Convert to proper dtype
        for col, dtype in listdtype:
            if dtype in ["float", "int"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif dtype == "datetime":
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df

    # -------------------- Load Data --------------------
    query = "SELECT * FROM TRAIN_VOLUME;"
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int"),
                 ("train_volume_year_month", "datetime")]
    df = run_query(query, listdtype)

    if df.empty:
        st.error("❌ No data returned from database.")
        return

    # Encode day type
    df["train_volume_day"] = df["train_volume_day"].map({"WEEKDAY": 0, "WEEKENDS/HOLIDAY": 1})

    # -------------------- Train/Test Split --------------------
    df["year_month_period"] = df["train_volume_year_month"].dt.to_period("M")
    months = df["year_month_period"].unique()

    if len(months) < 2:
        st.error("❌ Not enough months of data to split into train/test")
        return

    train_month = months[-2]  # second last month
    test_month = months[-1]   # last month

    train = df[df["year_month_period"] == train_month].copy()
    test = df[df["year_month_period"] == test_month].copy()

    # -------------------- Feature Engineering --------------------
    # Drop rows with missing key features
    train = train.dropna(subset=["train_volume_tap_in", "train_volume_hour", "train_code", "train_volume_day"])
    test  = test.dropna(subset=["train_volume_tap_in", "train_volume_hour", "train_code", "train_volume_day"])

    # One-hot encode categorical variables
    train = pd.get_dummies(train, columns=["train_code", "train_volume_hour"], drop_first=True)
    test = pd.get_dummies(test, columns=["train_code", "train_volume_hour"], drop_first=True)

    # Align columns
    test = test.reindex(columns=train.columns, fill_value=0)

    # Lag feature: previous tap-in
    train["lag_1"] = train["train_volume_tap_in"].shift(1)
    test["lag_1"] = pd.concat([train["train_volume_tap_in"].iloc[-1:], test["train_volume_tap_in"]]).shift(1).iloc[1:]

    # Drop rows with NaN lag
    train = train.dropna()
    test = test.dropna()

    # -------------------- Prepare X/y --------------------
    X_train = train.drop(columns=["train_volume_tap_in", "train_volume_year_month", "year_month_period"])
    y_train = train["train_volume_tap_in"]
    X_test  = test.drop(columns=["train_volume_tap_in", "train_volume_year_month", "year_month_period"])
    y_test  = test["train_volume_tap_in"]

    # -------------------- Train Model --------------------
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # -------------------- Metrics --------------------
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    st.subheader("📊 Regression Metrics")
    st.write(f"MSE: {mse:.2f}")
    st.write(f"MAE: {mae:.2f}")
    st.write(f"R²: {r2:.2f}")

    # -------------------- Visualization --------------------
    st.subheader("📈 Actual vs Predicted Tap-In Volume")

    plt.figure(figsize=(12,6))
    plt.plot(y_test.values, label="Actual", marker='o')
    plt.plot(y_pred, label="Predicted", marker='x')
    plt.xlabel("Index")
    plt.ylabel("Tap-In Volume")
    plt.title("Regression Forecast per Train Tap-In")
    plt.legend()
    st.pyplot(plt)

    # Optional: Station-level visualization
    st.subheader("🚉 Station-level Tap-In Comparison")
    if "train_code_" in X_train.columns[0]:  # check if one-hot encoding applied
        station_cols = [c for c in X_train.columns if c.startswith("train_code_")]
        for s_col in station_cols[:5]:  # show top 5 for brevity
            plt.figure(figsize=(10,4))
            plt.plot(train[s_col].values, label=f"Train {s_col} (Train Month)")
            plt.plot(test[s_col].values, label=f"Train {s_col} (Test Month)")
            plt.title(f"Station {s_col} Tap-In Indicator")
            plt.legend()
            st.pyplot(plt)


