import streamlit as st
import pandas as pd
import os

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
