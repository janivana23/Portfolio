import streamlit as st
import pandas as pd
import mysql.connector
import pydeck as pdk
import math
import re

st.title("🚇 MRT Station Map")


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


# --- Fetch data ---

if st.session_state.connected:
    conn = st.session_state.conn
    cur = conn.cursor()
    
    @st.cache_data
    def run_query(query):
        cur = conn.cursor()
        cur.execute(query)
        cols = [col[0] for col in cur.description]
        rows = cur.fetchall()
        df = pd.DataFrame(rows, columns=cols)
        df.columns = df.columns.str.upper()

        for col in df.columns:
            if pd.api.types.is_object_dtype(df[col]):
                try:
                    df[col] = pd.to_datetime(df[col])
                except Exception:
                    pass
        if 'TRAIN_STATION_ADDRESS' in df.columns:
            df['postcode'] = df['TRAIN_STATION_ADDRESS'].apply(
                lambda x: re.search(r'\b\d{6}\b', x).group() if re.search(r'\b\d{6}\b', x) else None
            )
        return df

    # Table with coordinates
    query = f"SELECT * FROM TRAIN_STATION NATURAL JOIN TRAIN NATURAL JOIN URA"
    df = run_query(query)

    # Sidebar filters
    st.sidebar.header("Map Filters")
    filtered_df = df.copy()

    for idx, col in enumerate(df.columns):
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            years = df[col].dt.year.unique()
            selected_years = st.sidebar.multiselect(f"Select {col} Year(s)", sorted(years), key=f"map_filter_{col}_{idx}")
            if selected_years:
                filtered_df = filtered_df[filtered_df[col].dt.year.isin(selected_years)]
        elif col == 'TRAIN_STATION_ADDRESS' and 'postcode' in df.columns:
            postcodes = sorted(df['postcode'].dropna().unique())
            selected_postcodes = st.sidebar.multiselect(f"Select Postcode(s)", postcodes, key=f"map_filter_postcode_{idx}")
            if selected_postcodes:
                filtered_df = filtered_df[filtered_df['postcode'].isin(selected_postcodes)]
        elif col == 'URA_AREA':
            areas = sorted(df['URA_AREA'].dropna().unique())
            selected_areas = st.sidebar.multiselect(f"Select URA Area(s)", areas, key=f"map_filter_ura_area_{idx}")
            if selected_areas:
                filtered_df = filtered_df[filtered_df['URA_AREA'].isin(selected_areas)]

        elif col == 'URA_REGION':
            areas = sorted(df['URA_REGION'].dropna().unique())
            selected_areas = st.sidebar.multiselect(f"Select URA Region(s)", areas, key=f"map_filter_ura_region_{idx}")
            if selected_areas:
                filtered_df = filtered_df[filtered_df['URA_REGION'].isin(selected_areas)]

        elif col == 'TRAIN_LINE_NAME':
            areas = sorted(df['TRAIN_LINE_NAME'].dropna().unique())
            selected_areas = st.sidebar.multiselect(f"Select Train Line(s)", areas, key=f"map_filter_train_line_{idx}")
            if selected_areas:
                filtered_df = filtered_df[filtered_df['TRAIN_LINE_NAME'].isin(selected_areas)]


    # Map visualization
    if 'TRAIN_STATION_LAT' in filtered_df.columns and 'TRAIN_STATION_LONG' in filtered_df.columns:
        st.subheader("Interactive MRT Station Map")

        # Rename for pydeck
        map_df = filtered_df.rename(columns={'TRAIN_STATION_LAT':'lat','TRAIN_STATION_LONG':'lon'})

        color_by = st.sidebar.selectbox(
            "Color dots by",
            options=['URA_REGION', 'TRAIN_LINE_NAME'],
            index=0  # default
        )
        
        # Get unique values based on color_by selection
        unique_values = map_df[color_by].dropna().unique()

        if color_by == 'TRAIN_LINE_NAME':
            # Train line to official MRT color
            color_map = {
                'Circle Line': [250, 158, 13],                       # Circle Line
                'Circle Line Extension': [250, 158, 13],             # Circle Line Extension
                'Changi Airport Branch Line': [0, 150, 69],          # East–West Line – Changi Airport Line
                'Downtown Line': [0, 94, 196],                       # Downtown Line
                'East-West Line': [0, 150, 69],                      # East–West Line
                'North East Line': [153, 0, 170],                    # North East Line
                'North-South Line': [212, 46, 18],                   # North–South Line
                'Thomson-East Coast Line': [157, 91, 37],            # Thomson–East Coast Line
                'Punggol LRT': [128, 128, 128],                      # Grey for LRT
                'Sengkang LRT': [128, 128, 128],                     # Grey for LRT
                'Bukit Panjang LRT': [128, 128, 128],                # Grey for LRT
                'LRT' :[128, 128, 128]
            }
            # Mapping extensions to their main line
            line_merge_map = {
                'Circle Line Extension': 'Circle Line',
                'Changi Airport Branch Line': 'East-West Line',
                'Punggol LRT': 'LRT',
                'Sengkang LRT': 'LRT',
                'Bukit Panjang LRT': 'LRT'
            }
            # Replace extension names with main line
            map_df['line_for_color'] = map_df['TRAIN_LINE_NAME'].apply(
                lambda x: line_merge_map.get(x, x)
            )

            # Map the selected column to color (TRAIN LINE)
            map_df['color'] = map_df['line_for_color'].map(color_map)
            unique_lines = map_df['line_for_color'].dropna().unique()
            color_map = {line: color_map.get(line, [128,128,128]) for line in unique_lines}

            #Header Legend for TRAIN LINE
            st.subheader("Train Line Legend")

        elif color_by == 'URA_REGION':
            # Assign colors dynamically
            colors = [
                [255,0,0], [0,255,0], [0,0,255], [255,255,0],
                [255,0,255], [128,128,128], [0,255,255], [255,128,0]
            ]
            color_map = {val: colors[i % len(colors)] for i, val in enumerate(unique_values)}
            # Map the selected column to color (URA REGION)
            map_df['color'] = map_df[color_by].map(color_map)

            #Header Legend for URA REGION
            st.subheader("URA Region Legend")
            

        # Determine number of columns per row
        cols_per_row = 4  # adjust based on screen width

        # Split legend items into rows
        rows = math.ceil(len(color_map) / cols_per_row)
        lines_list = list(color_map.items())

        for r in range(rows):
            start = r * cols_per_row
            end = start + cols_per_row
            cols = st.columns(cols_per_row)

            for i, (line, color) in enumerate(lines_list[start:end]):
                hex_color = '#%02x%02x%02x' % tuple(color)
                cols[i].markdown(
                    f"""
                    <div style='background-color:{hex_color};
                                width:140px;
                                height:50px;
                                display:flex;
                                align-items:center;
                                justify-content:center;
                                border-radius:5px;
                                text-align:center;
                                font-weight:bold;
                                margin:2px'>
                        {line}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Dynamic center & zoom
        center_lat = map_df['lat'].mean()
        center_lon = map_df['lon'].mean()
        lat_range = map_df['lat'].max() - map_df['lat'].min()
        lon_range = map_df['lon'].max() - map_df['lon'].min()
        zoom_level = max(15 - max(lat_range, lon_range)*100, 10)

        # --- FIX: make map_df JSON-serializable ---
        for col in map_df.columns:
            if pd.api.types.is_datetime64_any_dtype(map_df[col]):
                map_df[col] = map_df[col].astype(str)
            elif pd.api.types.is_integer_dtype(map_df[col]):
                map_df[col] = map_df[col].astype(int)
            elif pd.api.types.is_float_dtype(map_df[col]):
                map_df[col] = map_df[col].astype(float)

        st.write("Column dtypes before map:", map_df.dtypes)
        st.write(map_df.head(3).to_dict())

        #PyDeck Map
        st.pydeck_chart(pdk.Deck(
            map_style='light',
            initial_view_state=pdk.ViewState(
                latitude=center_lat,
                longitude=center_lon,
                zoom=zoom_level,
                pitch=0,
            ),
            layers=[
                pdk.Layer(
                    'ScatterplotLayer',
                    data=map_df,
                    get_position='[lon, lat]',
                    get_fill_color='color',
                    get_radius=150,
                    pickable=True
                )
            ],
            tooltip={
                "html": "<b>Station:</b> {TRAIN_NAME} <br/> <b>Line:</b> {TRAIN_LINE_NAME} <br/> <b>Address:</b> {TRAIN_STATION_ADDRESS} <br/> <b>Region:</b> {URA_REGION}",
                "style": {"color": "white"}
            }
        ))
        st.subheader("Data Viewing")
        # Drop postcode column before displaying
        st.dataframe(map_df, use_container_width=True)
    else:
        st.info("No latitude/longitude data available for mapping.")



    st.write("This is an interactive map displaying the locations of MRT stations in Singapore, data collected in January 2025")
