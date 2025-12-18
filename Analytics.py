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




    # -------------------- Load aggregated station data --------------------
    query2 = "SELECT train_code, train_name, SUM(train_volume_tap_in) AS total_volume_in, SUM(train_volume_tap_out) AS total_volume_out FROM TRAIN NATURAL JOIN TRAIN_VOLUME GROUP BY train_code, train_name ORDER BY total_volume_in DESC, total_volume_out DESC;"

    listdtype = [
        ("total_volume_in", "int"),
        ("total_volume_out", "int")
    ]

    df = run_query(query2, listdtype)
    df.columns = df.columns.str.lower()

    # Calculate total_volume for plotting
    df["total_volume"] = df["total_volume_in"] + df["total_volume_out"]

    # -------------------- Top 10 Busiest Stations --------------------
    st.subheader("Top 10 Busiest Stations")

    top10 = df.nlargest(10, "total_volume")
    fig, ax = plt.subplots(figsize=(10,5))
    ax.bar(top10["train_name"], top10["total_volume"], color="skyblue")
    ax.set_ylabel("Total Volume")
    ax.set_title("Top 10 Busiest Stations")
    plt.xticks(rotation=45, ha="right")
    st.pyplot(fig)

    # -------------------- Tap-in vs Tap-out by Station --------------------
    st.subheader("Tap-in vs Tap-out by Station")

    fig, ax = plt.subplots(figsize=(10,7))
    ax.scatter(df["total_volume_in"], df["total_volume_out"], color="dodgerblue", alpha=0.7)

    # Annotate top 10 stations
    texts = []
    for _, row in top10.iterrows():
        texts.append(
            ax.text(
                row["total_volume_in"], row["total_volume_out"], 
                row["train_name"], fontsize=8
            )
        )

    adjust_text(
        texts, ax=ax,
        expand_text=(1.2, 1.4),
        expand_points=(1.2, 1.4),
        force_text=(0.5, 1.0),
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
