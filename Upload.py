import streamlit as st
import mysql.connector
import pandas as pd


def app():
    st.title("Upload CSV to Oracle")

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

    cur = conn.cursor()    

    uploaded_file = st.file_uploader("Choose CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip().str.upper().str.replace(" ", "_")

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
        for col in ["TOTAL_TAP_IN_VOLUME", "TOTAL_TAP_OUT_VOLUME", "TIME_PER_HOUR"]:
            df_expanded[col] = pd.to_numeric(df_expanded[col], errors="coerce")
            df_expanded[col] = df_expanded[col].fillna(0).astype(int)

        df_expanded["YEAR_MONTH"] = pd.to_datetime(df_expanded["YEAR_MONTH"], errors="coerce")

        st.write("Preview of current database in TRAIN VOLUME:")
        query = "SELECT * FROM TRAIN_VOLUME"
        cur.execute(query)
        rows_qty = cur.fetchall()
        st.write(f"Total rows currently: {len(rows_qty)}")
        st.dataframe(rows_qty)

        rows_qty = len(df_expanded)
        st.write("Preview after splitting multi-line train codes:")
        st.write(f"Total rows after splitting: {rows_qty}")

        st.dataframe(df_expanded.head())

        st.write ("Make sure your csv file heading is listed below in order:")
        st.write("YEAR_MONTH, DAY_TYPE, TIME_PER_HOUR, PT_CODE, TOTAL_TAP_IN_VOLUME, TOTAL_TAP_OUT_VOLUME")
        if st.button("Insert into TRAIN_VOLUME"):

            try:
                for _, row in df_expanded.iterrows():
                    cur.execute("""
                        INSERT INTO TRAIN_VOLUME (
                            TRAIN_VOLUME_YEAR_MONTH,
                            TRAIN_VOLUME_DAY,
                            TRAIN_VOLUME_HOUR,
                            TRAIN_CODE,
                            TRAIN_VOLUME_TAP_IN,
                            TRAIN_VOLUME_TAP_OUT
                        )
                            
                                
                        VALUES (%s, %s, %s, %s, %s, %s)
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
            except mysql.connector.Error as err:
                st.error(f"MySQL error: {err}")
                print(f"MySQL error: {err}")  # log to console
            

