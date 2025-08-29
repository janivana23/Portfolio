import streamlit as st
import mysql.connector
import pandas as pd

st.title("Upload CSV to Oracle")

# --- Step 1: Get credentials ---
if "connected" not in st.session_state:
    st.session_state.connected = False

if not st.session_state.connected:
    with st.form("db_form"):
        user = st.text_input("Username")
        password = st.text_input("Password", type="password")
        host = st.text_input("Host", value="127.0.0.1")   # MySQL uses host instead of DSN
        submit = st.form_submit_button("Connect")

    if submit:
        try:
            conn = mysql.connector.connect(
                user=user,
                password=password,
                host=host,
                database="singapore_mrt_db"  # database name
            )
            st.session_state.conn = conn
            st.session_state.connected = True
            st.success("✅ Connected to MySQL Database!")
        except mysql.connector.Error as e:
            st.error(f"Database connection failed: {e}")

# --- Step 2: Upload CSV ---
if st.session_state.connected:
    conn = st.session_state.conn
    cur = conn.cursor()

    uploaded_file = st.file_uploader("Choose CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
                # Normalize column names
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")
        st.write("Preview of uploaded CSV:")
        st.dataframe(df.head())

        # Split multi-line train codes into separate rows
        new_rows = []
        for _, row in df.iterrows():
            codes = str(row["PT_CODE"]).split("/")  # split by slash
            for code in codes:
                new_rows.append({
                    "YEAR_MONTH": row["YEAR_MONTH"],
                    "DAY_TYPE": row["DAY_TYPE"],
                    "TIME_PER_HOUR": row["TIME_PER_HOUR"],
                    "PT_CODE": code.strip(),
                    "TOTAL_TAP_IN_VOLUME": row["TOTAL_TAP_IN_VOLUME"],
                    "TOTAL_TAP_OUT_VOLUME": row["TOTAL_TAP_OUT_VOLUME"]
                })
        df_expanded = pd.DataFrame(new_rows)
        rows_qty = len(df_expanded)
        st.write("Preview after splitting multi-line train codes:")
        st.write(f"Total rows after splitting: {rows_qty}")
        
        st.dataframe(df_expanded.head())

        st.write ("Make sure your csv file heading is listed below in order:")
        st.write("YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_CODE, TOTAL_TAP_IN_VOLUME, TOTAL_TAP_OUT_VOLUME")
        if st.button("Insert into TRAIN_VOLUME"):
            for _, row in df_expanded.iterrows():
                cur.execute("""
                    INSERT INTO TRAIN_VOLUME (
                        train_volume_year_month,
                        train_volume_day,
                        train_volume_hour,
                        train_code,
                        train_volume_tap_in,
                        train_volume_tap_out
                    ) VALUES (
                        STR_TO_DATE(:1, '%Y-%m-%d'),
                        :2, :3, :4, :5, :6
                    )
                """, (
                    row["YEAR_MONTH"],
                    row["DAY_TYPE"],
                    row["TIME_PER_HOUR"],
                    row["PT_CODE"],
                    row["TOTAL_TAP_IN_VOLUME"],
                    row["TOTAL_TAP_OUT_VOLUME"]
                ))
            conn.commit()
            st.success("✅ Data inserted into database!")
