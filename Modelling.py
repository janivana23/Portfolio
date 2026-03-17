import streamlit as st
import pandas as pd
import mysql.connector
import numpy as np
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Optional (best model)
try:
    from xgboost import XGBRegressor
    xgb_available = True
except:
    xgb_available = False


def app():
    # -------------------- Database Connection --------------------
    DB_USER = st.secrets["mysql"]["user"]
    DB_PASSWORD = st.secrets["mysql"]["password"]
    DB_HOST = st.secrets["mysql"]["host"]
    DB_NAME = st.secrets["mysql"]["database"]

    conn = mysql.connector.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        database=DB_NAME,
        port=3306
    )

    @st.cache_data
    def run_query(query):
        cur = conn.cursor()
        cur.execute(query)
        cols = [col[0] for col in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.lower()
        return df

    # -------------------- Load Data --------------------
    query = "SELECT * FROM TRAIN_VOLUME ORDER BY train_volume_year_month;"
    df = run_query(query)

    st.title("🚇 Singapore Train Station Modelling Analytics")

    # -------------------- Preprocessing --------------------
    df["train_volume_tap_in"] = pd.to_numeric(df["train_volume_tap_in"], errors="coerce")
    df["train_volume_hour"] = pd.to_numeric(df["train_volume_hour"], errors="coerce")
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"], errors="coerce")

    df["train_volume_day"] = df["train_volume_day"].map({
        "WEEKDAY": 0,
        "WEEKENDS/HOLIDAY": 1
    })

    df["train_code"] = df["train_code"].astype(str)

    # -------------------- Feature Engineering --------------------
    df = df.sort_values(["train_code", "train_volume_year_month", "train_volume_hour"])

    df["lag_1"]  = df.groupby("train_code")["train_volume_tap_in"].shift(1)
    df["lag_2"]  = df.groupby("train_code")["train_volume_tap_in"].shift(2)
    df["lag_24"] = df.groupby("train_code")["train_volume_tap_in"].shift(24)

    df["rolling_mean_3"] = (
        df.groupby("train_code")["train_volume_tap_in"]
        .shift(1)
        .rolling(3)
        .mean()
    )

    df = df.dropna()

    # -------------------- Train/Test Split --------------------
    months = sorted(df["train_volume_year_month"].dt.to_period("M").dropna().unique())

    if len(months) < 2:
        st.warning("⚠️ Only one month detected — using time-based split")
        df = df.sort_values("train_volume_year_month")
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx]
        test  = df.iloc[split_idx:]
    else:
        train_month, test_month = months[-2], months[-1]
        train = df[df["train_volume_year_month"].dt.to_period("M") == train_month]
        test  = df[df["train_volume_year_month"].dt.to_period("M") == test_month]

    # -------------------- Features --------------------
    features_num = [
        "train_volume_day",
        "train_volume_hour",
        "lag_1",
        "lag_2",
        "lag_24",
        "rolling_mean_3"
    ]

    target = "train_volume_tap_in"

    train = train.dropna(subset=features_num + ["train_code", target])
    test  = test.dropna(subset=features_num + ["train_code", target])

    if train.empty or test.empty:
        st.error("❌ Train/Test data is empty after preprocessing")
        st.stop()

    # -------------------- Encoding --------------------
    encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")

    X_train_cat = encoder.fit_transform(train[["train_code"]])
    X_test_cat  = encoder.transform(test[["train_code"]])

    X_train = np.hstack([train[features_num].values, X_train_cat])
    X_test  = np.hstack([test[features_num].values, X_test_cat])

    y_train = train[target].values
    y_test  = test[target].values

    # -------------------- Evaluation Function --------------------
    def evaluate(y_test, y_pred, test_df, model_name):
        mse = mean_squared_error(y_test, y_pred)
        mae = mean_absolute_error(y_test, y_pred)
        r2  = r2_score(y_test, y_pred)

        st.write(f"### {model_name}")
        st.write(f"MSE: {mse:.2f}")
        st.write(f"MAE: {mae:.2f}")
        st.write(f"R² (row-level): {r2:.2f}")

        # Aggregated evaluation
        hourly_test = test_df.groupby("train_volume_hour")[target].sum()
        hourly_pred = pd.Series(y_pred, index=test_df["train_volume_hour"]).groupby(level=0).sum()

        r2_hourly = r2_score(hourly_test, hourly_pred)
        st.write(f"R² (hourly aggregated): {r2_hourly:.2f}")

        # Plot
        plt.figure(figsize=(10,5))
        plt.plot(hourly_test.index, hourly_test.values, label="Actual", marker='o')
        plt.plot(hourly_pred.index, hourly_pred.values, label="Predicted", marker='x')
        plt.xlabel("Hour")
        plt.ylabel("Tap-In Volume")
        plt.title(f"{model_name} - Hourly Prediction")
        plt.legend()
        plt.grid(True)
        st.pyplot(plt)

    # -------------------- Random Forest --------------------
    rf = RandomForestRegressor(
        n_estimators=300,
        max_depth=15,
        min_samples_split=10,
        min_samples_leaf=5,
        max_features=0.7,
        n_jobs=-1,
        random_state=42
    )

    rf.fit(X_train, y_train)
    rf_pred = rf.predict(X_test)
    evaluate(y_test, rf_pred, test, "Random Forest")

    # -------------------- Gradient Boosting --------------------
    gb = GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=5,
        random_state=42
    )

    gb.fit(X_train, y_train)
    gb_pred = gb.predict(X_test)
    evaluate(y_test, gb_pred, test, "Gradient Boosting")

    # -------------------- XGBoost (Best) --------------------
    if xgb_available:
        xgb = XGBRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42
        )

        xgb.fit(X_train, y_train)
        xgb_pred = xgb.predict(X_test)
        evaluate(y_test, xgb_pred, test, "XGBoost 🚀")
    else:
        st.info("ℹ️ XGBoost not installed")