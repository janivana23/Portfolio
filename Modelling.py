import streamlit as st
import pandas as pd

import mysql.connector

from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

from statsmodels.tsa.arima.model import ARIMA

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

    st.write("X_train NaNs:", X_train.isna().sum())
    st.write("y_train NaNs:", y_train.isna().sum())
    st.write(df["train_volume_day"].unique())

    train_clean = train.dropna(subset=["train_volume_day", "train_volume_tap_in"])
    X_train = train_clean[["train_volume_day"]]
    y_train = train_clean["train_volume_tap_in"]

    # Regression Model
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("MSE:", mean_squared_error(y_test, y_pred))
    print("R²:", r2_score(y_test, y_pred))

    
    daily_train = train.set_index("train_volume_year_month")["train_volume_tap_in"].resample("D").sum()
    daily_test  = test.set_index("train_volume_year_month")["train_volume_tap_in"].resample("D").sum()


    # --- 3. Forecast October ---
    forecast = model.fit(X_train, y_train).forecast(steps=len(daily_test))
    forecast = pd.Series(forecast, index=daily_test.index) 

    # Align on index
    y_true, y_pred = daily_test.align(forecast, join="inner")

    # Drop NaNs from both sides
    mask = (~y_true.isna()) & (~y_pred.isna())
    y_true = y_true[mask]
    y_pred = y_pred[mask]

    if len(y_true) == 0 or len(y_pred) == 0:
        st.error("⚠️ No valid overlapping non-NaN values between actual and forecast.")
    else:
        mse = mean_squared_error(y_true, y_pred)
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mse)

        st.write(f"MSE: {mse:.2f}")
        st.write(f"MAE: {mae:.2f}")
        st.write(f"RMSE: {rmse:.2f}")

        print(f"MSE: {mse:.2f}")
        print(f"MAE: {mae:.2f}")
        print(f"RMSE: {rmse:.2f}")

    # --- 5. Visualization ---
    plt.figure(figsize=(10,5))
    plt.plot(daily_train.index, daily_train, label="Train (Sept)")
    plt.plot(daily_test.index, daily_test, label="Actual (Oct)", color="black")
    plt.plot(forecast.index, forecast, label="Forecast (Oct)", color="red")
    plt.legend()
    plt.title("Forecast: Tap-In Volume")
    plt.show()
