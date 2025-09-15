import streamlit as st
import pandas as pd
import mysql.connector
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder
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

    # Encode day type
    df["train_volume_day"] = df["train_volume_day"].map({"WEEKDAY": 0, "WEEKENDS/HOLIDAY": 1})
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])

    # Split by last 2 months
    months = df["train_volume_year_month"].dt.to_period("M").unique()
    if len(months) < 2:
        st.error("❌ Not enough months to split train/test")
        return

    train_month, test_month = months[-2], months[-1]
    train = df[df["train_volume_year_month"].dt.to_period("M") == train_month]
    test  = df[df["train_volume_year_month"].dt.to_period("M") == test_month]

    # -------------------- Prepare Features --------------------
    features = ["train_volume_day", "train_volume_hour", "train_code"]
    target = "train_volume_tap_in"

    train_clean = train.dropna(subset=features + [target])
    test_clean = test.dropna(subset=features + [target])

    # One-hot encode categorical features
    encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
    X_train_cat = encoder.fit_transform(train_clean[["train_code"]])
    X_test_cat  = encoder.transform(test_clean[["train_code"]])

    # Combine numeric + encoded categorical
    X_train = np.hstack([train_clean[["train_volume_day", "train_volume_hour"]].values, X_train_cat])
    X_test  = np.hstack([test_clean[["train_volume_day", "train_volume_hour"]].values, X_test_cat])

    y_train = train_clean[target].values
    y_test  = test_clean[target].values

    # -------------------- Random Forest Model --------------------
    st.subheader("Regression Model: Random Forest")
    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # -------------------- Evaluation --------------------
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    st.write(f"MSE: {mse:.2f}")
    st.write(f"MAE: {mae:.2f}")
    st.write(f"R²: {r2:.2f}")

    # -------------------- Visualization --------------------
    plt.figure(figsize=(10,5))
    plt.plot(test_clean["train_volume_year_month"], y_test, label="Actual", color="black")
    plt.plot(test_clean["train_volume_year_month"], y_pred, label="Predicted", color="red")
    plt.legend()
    plt.title("Random Forest Forecast: Tap-In Volume")
    st.pyplot(plt)


#-----------------------------------------------------------------------------------------

# -------------------- Gradient Boosting Model --------------------
    st.subheader("Regression Model: Gradient Boosting")
    model = GradientBoostingRegressor(
        n_estimators=300, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # -------------------- Evaluation --------------------
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2  = r2_score(y_test, y_pred)

    st.write(f"MSE: {mse:.2f}")
    st.write(f"MAE: {mae:.2f}")
    st.write(f"R²: {r2:.2f}")

    # -------------------- Visualization --------------------
    plt.figure(figsize=(12,6))

    # Plot actual tap-in volumes
    plt.plot(test_clean["train_volume_year_month"], y_test, 
            label="Actual", color="black", marker='o', linestyle='-', alpha=0.7)

    # Plot predicted tap-in volumes
    plt.plot(test_clean["train_volume_year_month"], y_pred, 
            label="Predicted", color="red", marker='x', linestyle='--', alpha=0.8)

    # Optional: add rolling average for smoother trend (7-day window)
    rolling_actual = pd.Series(y_test, index=test_clean["train_volume_year_month"]).rolling(window=7).mean()
    rolling_pred   = pd.Series(y_pred, index=test_clean["train_volume_year_month"]).rolling(window=7).mean()
    plt.plot(rolling_actual.index, rolling_actual, label="Actual (7-day avg)", color="blue", linewidth=2, alpha=0.6)
    plt.plot(rolling_pred.index, rolling_pred, label="Predicted (7-day avg)", color="orange", linewidth=2, alpha=0.6)

    plt.xlabel("Date")
    plt.ylabel("Tap-In Volume")
    plt.title("🚇 Gradient Boosting Forecast: Tap-In Volume")
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)
