import streamlit as st

def app():
    st.title("Information & Data Overview")

    st.markdown(
        """
        This page provides background information about the dashboard,  
        including data sources, geographical context, and project credits.
        """
    )

    st.divider()

    # ==============================
    # Project Overview
    # ==============================
    st.header("Project Overview")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            """
            🚇 **Scope**  
            Analysis of Singapore MRT ridership patterns across stations,
            time periods, and train lines.
            """
        )

    with col2:
        st.info(
            """
            🗺️ **Geographical Focus**  
            Station-level analysis using latitude, longitude,
            station address, and URA planning regions.
            """
        )

    with col3:
        st.info(
            """
            📊 **Analytical Focus**  
            Exploratory analysis, temporal trends, geospatial insights,
            and predictive modelling.
            """
        )

    # ==============================
    # Dashboard Structure
    # ==============================
    st.divider()
    st.header("Dashboard Structure")

    st.markdown(
        """
        The dashboard is organised into the following sections:

        - **Geospatial Overview**  
          Interactive map displaying MRT station locations, URA regions,
          and surrounding geographical context.

        - **Ridership Analytics**  
          Hourly, daily, and station-level ridership trends, including
          comparisons between tap-in and tap-out volumes (Data Inclusive from September 2023 - October 2023).

        - **Predictive Modelling**  
          Machine learning models used to explore and forecast ridership behaviour.

        - **Information & Credits**  
          Data description, sources, and project acknowledgements.
        """
    )

    # ==============================
    # Geographical & Station Data
    # ==============================
    st.divider()
    st.header("Geographical & Station Information")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            **Station Attributes Included:**
            - MRT station name  
            - Station address  
            - Latitude and longitude  
            - Train line  
            - URA planning region  
            """
        )

    with col2:
        st.markdown(
            """
            **Geospatial Use Cases:**
            - Visualising station distribution across Singapore  
            - Identifying regional demand patterns  
            - Comparing ridership intensity by location  
            """
        )

    # ==============================
    # Data Source
    # ==============================
    st.divider()
    st.header("Data Source")

    st.markdown(
        """
        The dataset used in this dashboard contains aggregated MRT ridership
        information and station metadata.

        **Key Characteristics:**
        - Public transport ridership data  
        - Time-based attributes (hour, date)  
        - Station-level aggregation  
        - No personally identifiable information (PII)  

        The data is intended for **educational, analytical, and research purposes**.
        """
    )

    # ==============================
    # Credits & Disclaimer
    # ==============================
    st.divider()
    st.header("Credits & Disclaimer")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            """
            **Developed By:**  
            Janice Ivana  

            **Field of Study:**  
            Computer Science / Data Science  

            **Purpose:**  
            Academic project and data analytics portfolio
            """
        )

    with col2:
        st.warning(
            """
            ⚠️ **Disclaimer**  
            This dashboard is for analytical and educational use only.
            Visualisations and models do not represent official transport
            forecasts or policy recommendations.
            """
        )
