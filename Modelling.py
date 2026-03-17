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

    conn = mysql.connector.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=DB_NAME,
        port=DB_PORT
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
    query = "SELECT * FROM TRAIN_VOLUME order by train_volume_year_month;"
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int"), ("train_volume_hour", "int"),("train_volume_year_month", "datetime")]
    df = run_query(query, listdtype)

    st.title("🚇 Singapore Train Station Modelling Analytics")

    # Encode day type
    df["train_volume_day"] = df["train_volume_day"].map({"weekday": 0, "weekends/holiday": 1})
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])

    months = sorted(df["train_volume_year_month"].dt.to_period("M").dropna().unique())

    st.write("Detected months:", months)

    if len(months) < 2:
        st.warning("⚠️ Not enough months — switching to random split")

        from sklearn.model_selection import train_test_split
        train, test = train_test_split(df, test_size=0.2, random_state=42)

    else:
        train_month, test_month = months[-2], months[-1]
        train = df[df["train_volume_year_month"].dt.to_period("M") == train_month]
        test  = df[df["train_volume_year_month"].dt.to_period("M") == test_month]

    st.write("Train shape:", train_clean.shape)
    st.write("Test shape:", test_clean.shape)

    st.write("Train train_code nulls:", train_clean["train_code"].isna().sum())
    st.write("Unique train_code (train):", train_clean["train_code"].nunique())

    st.write(train_clean.head())
    
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
    model = RandomForestRegressor(
        n_estimators=500,
        max_depth=None,  # unlimited depth
        max_features='sqrt',  # better generalization
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
    # Aggregate by hour
    hourly_test = test_clean.groupby("train_volume_hour")["train_volume_tap_in"].sum()
    hourly_pred = pd.Series(y_pred, index=test_clean["train_volume_hour"]).groupby(level=0).sum()

    plt.figure(figsize=(10,5))
    plt.plot(hourly_test.index, hourly_test.values, label="Actual", marker='o', linestyle='-', color='black')
    plt.plot(hourly_pred.index, hourly_pred.values, label="Predicted", marker='x', linestyle='--', color='red')
    plt.xlabel("Hour of Day")
    plt.ylabel("Tap-In Volume")
    plt.title("🚇 Hourly Tap-In Forecast (Random Forest)")
    plt.xticks(range(0,24))
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)


#-----------------------------------------------------------------------------------------

# -------------------- Gradient Boosting Model --------------------
    st.subheader("Regression Model: Gradient Boosting")
    model = GradientBoostingRegressor(
        n_estimators=500, 
        learning_rate=0.1, 
        max_depth=10, 
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
    # Aggregate by hour
    hourly_test = test_clean.groupby("train_volume_hour")["train_volume_tap_in"].sum()
    hourly_pred = pd.Series(y_pred, index=test_clean["train_volume_hour"]).groupby(level=0).sum()

    plt.figure(figsize=(10,5))
    plt.plot(hourly_test.index, hourly_test.values, label="Actual", marker='o', linestyle='-', color='black')
    plt.plot(hourly_pred.index, hourly_pred.values, label="Predicted", marker='x', linestyle='--', color='red')
    plt.xlabel("Hour of Day")
    plt.ylabel("Tap-In Volume")
    plt.title("🚇 Hourly Tap-In Forecast (Gradient Boosting)")
    plt.xticks(range(0,24))
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend()
    plt.tight_layout()
    st.pyplot(plt)
