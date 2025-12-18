import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import mysql.connector
from adjustText import adjust_text


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
    query1 = "SELECT * FROM TRAIN_STATION NATURAL JOIN TRAIN NATURAL JOIN URA"
    listdtype = [("train_station_lat", "float"), ("train_station_long", "float"), ("train_start_operation", "datetime")]
    df = run_query(query1, listdtype)

    st.title("🚇 Singapore Train Station Visual Analytics")

    # --- Stations Opened per Year ---
    st.subheader("Stations Opened per Year")

    stations_per_year = df.groupby(df['train_start_operation'].dt.year).size()

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
    query2 = "SELECT train_code, train_name, sum(train_volume_tap_in)as total_volume_in, sum(train_volume_tap_out) as total_volume_out  FROM TRAIN NATURAL JOIN TRAIN_VOLUME group by train_code, train_name order by total_volume_in desc, total_volume_out desc;"
    listdtype = [("train_volume_tap_in", "int"), ("train_volume_tap_out", "int"), ("train_start_operation", "datetime")]

    # df = run_query(query2, listdtype)
    df.columns = df.columns.str.lower()

    # --- Top 10 Busiest Stations ---
    st.subheader("Top 10 Busiest Stations")

    df = run_query(query2, listdtype=[("total_volume_in", "int"), ("total_volume_out", "int")])
    df.columns = df.columns.str.lower()
    df["total_volume"] = df["total_volume_in"] + df["total_volume_out"]
    top10 = df.groupby(["train_code", "train_name"])["total_volume"].sum().nlargest(10)

    fig, ax = plt.subplots()
    top10.plot(kind="bar", ax=ax)
    ax.set_ylabel("Total Volume")
    ax.set_title("Top 10 Busiest Stations")
    st.pyplot(fig)

    # --- Tap-in vs Tap-out by Station ---
    st.subheader("Tap-in vs Tap-out by Station")

    station_vol = df.groupby(["train_code", "train_name"])[["train_volume_tap_in", "train_volume_tap_out"]].sum()
    station_vol["total_volume"] = station_vol["train_volume_tap_in"] + station_vol["train_volume_tap_out"]

    # Take top 10 stations
    top10 = station_vol.sort_values("total_volume", ascending=False).head(10)

    fig, ax = plt.subplots()
    ax.scatter(station_vol["train_volume_tap_in"], station_vol["train_volume_tap_out"])

    texts = []
    for station, row in top10.iterrows():
        texts.append(
            ax.text(row["train_volume_tap_in"], row["train_volume_tap_out"], station, fontsize=6)
        )

    # increase expand_text and force_text to push labels further
    adjust_text(
        texts, 
        ax=ax,
        expand_text=(1.2, 1.4),   # push labels further from each other
        expand_points=(1.2, 1.4), 
        force_text=(0.5, 1.0),    # stronger repulsion between labels
        arrowprops=dict(arrowstyle="->", color="gray", lw=0.5)
    )

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
