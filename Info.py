import streamlit as st

def app():
    st.title("ℹ️ Information, Geography & Data Context")

    # -------------------- Dashboard Purpose --------------------
    st.header("Dashboard Purpose")
    st.markdown(
        """
        This dashboard provides an integrated analytical view of Singapore MRT ridership
        by combining **geospatial station information** with **hourly passenger volume data** inclusive from September 2023 to October 2023.

        It is designed to support:
        - Understanding spatial distribution of ridership demand
        - Identifying high-traffic stations and regions
        - Exploring temporal travel patterns across the rail network
        - Demonstrating applied data analytics and geospatial visualisation techniques
        """
    )

    # -------------------- Geospatial Data & Map --------------------
    st.header("Geospatial Mapping")
    st.markdown(
        """
        The interactive map component visualises MRT stations using geographic coordinates.
        Each station is positioned based on latitude and longitude and enriched with
        contextual metadata.

        **Mapped attributes include:**
        - Train station name and code
        - Physical station address
        - URA planning region
        - MRT line affiliation
        - Aggregated ridership indicators

        The map enables spatial comparison of stations and highlights how ridership demand
        varies across different regions of Singapore.
        """
    )

    # -------------------- Station Metadata --------------------
    st.header("Station Information")
    st.markdown(
        """
        Each train station is associated with descriptive metadata that provides
        real-world context beyond passenger counts.

        **Station-level information includes:**
        - Station name and station code
        - Official address
        - URA planning region
        - MRT line name
        - Operational status and service coverage

        This information allows users to relate ridership patterns to
        land use, urban density, and regional activity.
        """
    )

    # -------------------- URA Planning Regions --------------------
    st.header("URA Planning Regions")
    st.markdown(
        """
        Stations are categorised by **URA Planning Region**, which reflects Singapore’s
        official urban planning structure.

        Examples include:
        - Central Region
        - East Region
        - North Region
        - North-East Region
        - West Region

        Grouping stations by URA region enables higher-level analysis of
        commuter movement and regional transport demand.
        """
    )

    # -------------------- Data Sources --------------------
    st.header("Data Sources")
    st.markdown(
        """
        The data used in this dashboard originates from publicly available and
        authoritative sources.

        **Primary sources include:**
        - Singapore public transport datasets (e.g. LTA / Data.gov.sg)
        - Kaggle

        All datasets are stored in a structured MySQL database and queried dynamically
        for analysis and visualisation.
        """
    )

    # -------------------- Data Processing & Assumptions --------------------
    st.header("Data Processing & Assumptions")
    st.markdown(
        """
        To ensure analytical consistency, the following steps were applied:

        - Removal of incomplete or invalid records
        - Standardisation of station names and codes
        - Aggregation of ridership data at hourly, station, and regional levels
        - Alignment of station metadata with ridership records via relational joins

        Some external factors such as weather conditions, special events,
        and service disruptions are not included in the dataset.
        """
    )

    # -------------------- Credits --------------------
    st.header("Credits & Acknowledgements")
    st.markdown(
        """
        **Developed by:**  
        Janice Ivana  

        **Tools & Technologies:**
        - Python
        - Streamlit
        - Pandas, NumPy
        - Matplotlib, Seaborn
        - Scikit-learn
        - MySQL
        - Geospatial mapping libraries

        **Acknowledgements:**
        - Singapore Land Transport Authority (LTA)
        - Urban Redevelopment Authority (URA)
        - Data.gov.sg
        - Open-source Python community
        """
    )

    # -------------------- Disclaimer --------------------
    st.header("Disclaimer")
    st.markdown(
        """
        This dashboard is developed for educational and analytical purposes only.
        It does not represent official transport statistics or policy decisions
        by any government authority.
        """
    )
