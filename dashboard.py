import streamlit as st
import pandas as pd
from helper import convert_types
from helper import _convert_series

data = pd.read_csv('Louisville_Metro_KY_-_Property_Foreclosures.csv')

data_types = [
    int, str, str, str, int, int, str, int, str, str,
    int, "datetime64[ns]", str, str, "datetime64[ns]", int, str, int
]

data = convert_types(data, data_types)


data = pd.read_csv('Louisville_Metro_KY_-_Property_Foreclosures.csv')

#title
st.markdown("# Roles Dashbaord")

#defining side bar
st.sidebar.header("Filters:")

#placing filters in the sidebar using unique values.
location = st.sidebar.multiselect(
    "Select Location:",
    options=data["Neighborhood"].dropna().unique(),
    default=data["Neighborhood"].dropna().unique()
    )