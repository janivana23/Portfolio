import streamlit as st
import pandas as pd
import os
import pandas as pd
import mysql.connector

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

df = pd.read_sql("SELECT * FROM TRAIN_VOLUME order by train_volume_year_month;", conn)
df.to_csv("trainvolume.csv", index=False)

conn.close()

def app():
    # Path to dataset folder
    DATASET_FOLDER = "dataset"

    st.title("📂 Dataset Downloader")

    # List all CSVs inside dataset folder
    csv_files = [f for f in os.listdir(DATASET_FOLDER) if f.endswith(".csv")]

    if csv_files:
        # Let user pick which file to download
        selected_file = st.selectbox("Choose a dataset to download:", csv_files)

        # Load file into DataFrame
        df = pd.read_csv(os.path.join(DATASET_FOLDER, selected_file))

        # Show preview
        st.dataframe(df.head())

        # Download button
        st.download_button(
            label="⬇️ Download this file",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=selected_file,
            mime="text/csv"
        )
    else:
        st.warning("No CSV files found in dataset folder.")
