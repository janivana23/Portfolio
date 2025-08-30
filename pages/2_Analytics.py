import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector

st.title("🚇 MRT Station Map")


# --- Step 1: Get credentials ---
if "connected" not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    with st.form("db_form"):
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        host = "singaporemrtserver.mysql.database.azure.com"
        port=3306
        submit = st.form_submit_button("Connect")

    if submit:
        try:
            conn = mysql.connector.connect(
                user=user,
                password=password,
                host=host,
                port=port,
                database="singapore_mrt_db"
            )
            st.session_state.conn = conn
            st.session_state.connected = True
            st.success("✅ Connected to MySQL Database!")
        except mysql.connector.Error as e:
            st.error(f"Database connection failed: {e}")



if st.session_state.connected:
    conn = st.session_state.conn
    cur = conn.cursor()
    @st.cache_data
    def run_query(query):
        cur = conn.cursor()
        cur.execute(query)
        cols = [col[0] for col in cur.description]  # column names
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.lower()
        # Ensure coordinates are float
        df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
        df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
        df["train_start_operation"] = pd.to_datetime(df["train_start_operation"], errors="coerce")

        return df

    #-----------------------------------------------------------------------------------------
    query1 = "SELECT * FROM TRAIN_STATION NATURAL JOIN TRAIN NATURAL JOIN URA"
    df = run_query(query1)


    st.write("Column dtypes", df.dtypes)
    st.write(df.head(3).to_dict())

    # --- Stations Opened per Year ---
    st.subheader("Stations Opened per Year")

    stations_per_year = df.groupby(df['train_start_operation']).size()

    fig, ax = plt.subplots()
    stations_per_year.plot(kind="bar", ax=ax)
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Stations Opened")
    ax.set_title("MRT & LRT Expansion Over Time")
    st.pyplot(fig)


    # --- Number of Stations by Line ---
    st.subheader("Number of Stations by Line")

    stations_per_line = df.groupby(df['train_line_name']).size().sort_values(ascending=False)

    fig, ax = plt.subplots()
    stations_per_line.plot(kind="barh", ax=ax)
    ax.set_xlabel("Number of Stations")
    ax.set_ylabel("Line")
    st.pyplot(fig)

    # --- Stations by City/Region ---
    st.subheader("Stations by Region")

    stations_by_region = df.groupby("ura_region").size().sort_values(ascending=False).head(10)

    fig, ax = plt.subplots()
    stations_by_region.plot(kind="bar", ax=ax)
    ax.set_xlabel("Region")
    ax.set_ylabel("Number of Stations")
    st.pyplot(fig)


    # ---------------------------------------------------------------------------------------
    query2 = "SELECT * FROM TRAIN NATURAL JOIN TRAIN_VOLUME"
    df = run_query(query2)
    df.columns = df.columns.str.lower()

    # --- Top 10 Busiest Stations ---
    st.subheader("Top 10 Busiest Stations")

    df["total_volume"] = df["train_volume_tap_in"] + df["train_volume_tap_out"]
    top10 = df.groupby("train_name")["total_volume"].sum().nlargest(10)

    fig, ax = plt.subplots()
    top10.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Volume")
    ax.set_title("Top 10 Busiest Stations")
    st.pyplot(fig)

    # --- Tap-in vs Tap-out by Station ---
    st.subheader("Tap-in vs Tap-out by Station")

    station_vol = df.groupby("train_name")[["train_volume_tap_in", "train_volume_tap_out"]].sum()

    fig, ax = plt.subplots()
    ax.scatter(station_vol["train_volume_tap_in"], station_vol["train_volume_tap_out"])

    for station, row in station_vol.iterrows():
        ax.annotate(station, (row["train_volume_tap_in"], row["train_volume_tap_out"]), fontsize=6)

    ax.set_xlabel("Tap-in Volume")
    ax.set_ylabel("Tap-out Volume")
    ax.set_title("Tap-in vs Tap-out by Station")
    st.pyplot(fig)


    # --- Ridership Trend Over Time ---
    st.subheader("Ridership Trend Over Time")

    daily_volume = df.groupby("train_volume_hour")["total_volume"].sum()

    fig, ax = plt.subplots()
    daily_volume.plot(ax=ax)
    ax.set_xlabel("Hour")
    ax.set_ylabel("Total Volume")
    ax.set_title("Daily Ridership Trend")
    st.pyplot(fig)


    # --- Hourly Ridership Heatmap by Line ---
    st.subheader("Hourly Ridership Heatmap by Line")

    line_hour = df.groupby(["train_line_name", "train_volume_hour"])["total_volume"].sum().unstack()

    fig, ax = plt.subplots(figsize=(10,6))
    sns.heatmap(line_hour, cmap="Blues", ax=ax)
    ax.set_title("Hourly Ridership by Line")
    st.pyplot(fig)
