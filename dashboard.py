import streamlit as st
import pandas as pd
import plotly.express as px
from helper import convert_types
from helper import _convert_series
from helper import build_address
from helper import safe_mode

############################################################################
# data loading and preprocessing
############################################################################

# Load data
data = pd.read_csv('Louisville_Metro_KY_-_Property_Foreclosures.csv')

# Define data types for conversion
data_types = [
    int, str, str, str, int, int, str, int, str, str,
    int, "datetime64[ns]", str, str, "datetime64[ns]", int, str, int
]

# Convert data types and build address
data = convert_types(data, data_types)
data = build_address(data)
data["Action_Year"] = data["Action_Filed"].dt.year

# Calculate year counts
yr_counts = data["Action_Year"].value_counts().sort_index(ascending=False)

############################################################################
# dashboard creation
############################################################################
st.set_page_config(
    page_title="Foreclosures Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# title
st.markdown("# Foreclosures in Louisville, KY")

############################################################################
# sidebar filters
############################################################################

# defining side bar
st.sidebar.header("Filters:")

# placing filters in the sidebar using unique values.
location = st.sidebar.multiselect(
    "Select Location:",
    options=data["Neighborhood"].dropna().unique(),
    default=data["Neighborhood"].dropna().unique()
)

# Sidebar filter for year
years_sorted = pd.Series(data["Action_Year"].dropna().unique()).sort_values(ascending=False)

year = st.sidebar.multiselect(
    "Select Year:",
    options=years_sorted,
    default=years_sorted
)

# Apply filters
filtered_data = data[
    (data["Neighborhood"].isin(location)) &
    (data["Action_Year"].isin(year))
]

############################################################################
# top cards
############################################################################

df = filtered_data.copy()

# --- 1. Total foreclosures ---
total_foreclosures = len(df)

# --- 2. Prepare Month columns if they exist ---
if "Action_Filed" in df.columns:
    df["Foreclosure_Month"] = pd.to_datetime(df["Action_Filed"], errors="coerce").dt.month_name()
else:
    df["Foreclosure_Month"] = pd.Series(dtype=str)

if "Sale_Date" in df.columns:
    df["Sale_Month"] = pd.to_datetime(df["Sale_Date"], errors="coerce").dt.month_name()
else:
    df["Sale_Month"] = pd.Series(dtype=str)

popular_zip = safe_mode(df["Zip"])
popular_foreclosure_month = safe_mode(df["Foreclosure_Month"])
popular_sale_month = safe_mode(df["Sale_Month"])
popular_purchaser = safe_mode(df["Purchaser"])

# --- Layout with metrics ---
with st.container():
    col1, col2, col3, col4, col5 = st.columns([1,1,1,1,1])
    col1.metric("Total Foreclosures", total_foreclosures)
    col2.metric("Top Zip Code", popular_zip)
    col3.metric("Peak Filing Month", popular_foreclosure_month)
    col4.metric("Peak Sale Month", popular_sale_month)
    col5.metric("Top Purchaser", popular_purchaser)

############################################################################
# bar chart
############################################################################
# plotting bar chart
nei_counts = filtered_data.groupby("Neighborhood").size().reset_index(name="count")
fig_count_location_type = px.bar(
    nei_counts,
    x="Neighborhood",
    y="count",
    title="Foreclosures by Neighborhood",
    labels={"count": "Number of Foreclosures", "Neighborhood": "Neighborhood"},
    color_discrete_sequence=["#0083B8"] * len(nei_counts),
    template="plotly_white"
)

st.plotly_chart(fig_count_location_type, use_container_width=True)

# dividing line
st.divider()

############################################################################
# display table 
############################################################################
# Convert dates to MMDDYYYY format
filtered_data['Action_Filed'] = pd.to_datetime(filtered_data['Action_Filed'], errors='coerce').dt.strftime('%m/%d/%Y')
filtered_data['Sale_Date'] = pd.to_datetime(filtered_data['Sale_Date'], errors='coerce').dt.strftime('%m/%d/%Y')
# Display selected columns in a clean format
filtered_data = filtered_data[['Address', 'Zip', 'Neighborhood', 'Action_Filed', 'Case_Style', 'Sale_Date', 'Purchaser']]

st.markdown("### Foreclosure Details")
st.write(filtered_data)
