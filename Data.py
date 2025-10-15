import streamlit as st
import pandas as pd
import mysql.connector
import re

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

    # --- Fetch data ---
    @st.cache_data
    def run_query(query):
        cur = conn.cursor()
        cur.execute(query)
        cols = [col[0] for col in cur.description]  # column names
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.upper()

        # Automatically convert object columns to datetime if possible
        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass

        if 'TRAIN_STATION_ADDRESS' in df.columns:
            df['postcode'] = df['TRAIN_STATION_ADDRESS'].apply(
                lambda x: re.search(r'\b\d{6}\b', str(x)).group() if re.search(r'\b\d{6}\b', str(x)) else None
            )

        return df

    # --- Streamlit UI ---
    st.title("🚇 MRT Portfolio Dashboard")
    st.header("Singapore Train Network Data Viewer")

    st.write("Select a table to view:")
    st.write("1. TRAIN\n2. URA\n3. TRAIN_STATION\n4. TRAIN_VOLUME")

    data_options = ['TRAIN', 'URA', 'TRAIN_STATION', 'TRAIN_VOLUME']
    table = st.text_input("Enter table name", "").upper()

    if table in data_options:
        query = f"SELECT * FROM {table}"
        df = run_query(query)

        # --- Sidebar Filters ---
        st.sidebar.header("Filters")
        selections = {}
        filtered_df = df.copy()

        for idx, col in enumerate(df.columns):
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                # Date column → filter by year
                years = df[col].dt.year.unique()
                selected_years = st.sidebar.multiselect(
                    f"Select {col} Year(s)", sorted(years), key=f"filter_{col}_{idx}"
                )
                selections[col] = selected_years
                if selected_years:
                    filtered_df = filtered_df[filtered_df[col].dt.year.isin(selected_years)]

            elif col == 'TRAIN_STATION_ADDRESS' and 'postcode' in df.columns:
                # Use postcode for filtering instead of full address
                postcodes = sorted(df['postcode'].dropna().unique())
                selected_postcodes = st.sidebar.multiselect(
                    "Select Postcode(s)", postcodes, key=f"filter_postcode_{idx}"
                )
                selections['postcode'] = selected_postcodes
                if selected_postcodes:
                    filtered_df = filtered_df[filtered_df['postcode'].isin(selected_postcodes)]

            elif col != 'postcode':
                opts = sorted(df[col].dropna().unique())
                selected_opts = st.sidebar.multiselect(
                    f"Select {col}", opts, key=f"filter_{col}_{idx}"
                )
                selections[col] = selected_opts
                if selected_opts:
                    filtered_df = filtered_df[filtered_df[col].isin(selected_opts)]

        # --- Display filtered & sorted data ---
        st.subheader("Data Viewing")
        # Drop postcode column before displaying
        display_df = filtered_df.drop(columns=['postcode'], errors='ignore')

        st.dataframe(display_df, use_container_width=True)

    elif table:
        st.error("Please enter a valid table name from the options above.")
