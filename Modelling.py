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
    query = "SELECT * FROM TRAIN_VOLUME;"  # adjust columns as needed
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int")]
    df = run_query(query, listdtype)

    st.title("🚇 Singapore Train Station Modelling Analytics")


    # Make sure that year month is datetime
    df["train_volume_year_month"] = pd.to_datetime(df["train_volume_year_month"])
    df = df.sort_values("train_volume_year_month")

    #Split data to train and test
    train = df[df["train_volume_year_month"].dt.month == 9]   # September 2023
    test  = df[df["train_volume_year_month"].dt.month == 10]  # October 2023

    # Create x and y train test
    y_train = train["TOTAL_TAP_IN_VOLUME"]
    y_test  = test["TOTAL_TAP_IN_VOLUME"]

    X_train = train[["train_volume_day"]]
    X_test  = test[["train_volume_day"]]

    # Regression Model
    model = LinearRegression()
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print("MSE:", mean_squared_error(y_test, y_pred))
    print("R²:", r2_score(y_test, y_pred))

    
    # Aggregate daily volume
    daily_train = train.set_index("DATE")["TOTAL_TAP_IN_VOLUME"]
    daily_test  = test.set_index("DATE")["TOTAL_TAP_IN_VOLUME"]

    # --- 2. Fit ARIMA model ---
    model = ARIMA(daily_train, order=(1,1,1), seasonal_order=(1,1,1,7))     
    model_fit = model.fit()

    # --- 3. Forecast October ---
    forecast = model_fit.forecast(steps=len(daily_test))
    forecast = pd.Series(forecast, index=daily_test.index)

    # --- 4. Evaluate ---
    mse = mean_squared_error(daily_test, forecast)
    mae = mean_absolute_error(daily_test, forecast)
    rmse = np.sqrt(mse)

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
