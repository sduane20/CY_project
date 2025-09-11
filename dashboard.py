import streamlit as st
import helper

############################################################################
# PAGE CONFIGURATION & DATA LOADING
############################################################################

st.set_page_config(
    page_title="Foreclosures Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load and preprocess data using the single helper function
data = helper.load_and_preprocess_data(
    'data/Louisville_Metro_KY_-_Property_Foreclosures.csv')

############################################################################
# SIDEBAR & FILTERING
############################################################################

st.sidebar.header("Filters:")

# Get filter options from the helper
locations_options, year_options = helper.get_filter_options(data)

# Create sidebar widgets
selected_locations = st.sidebar.multiselect(
    "Select Location:",
    options=locations_options,
    default=locations_options
)

selected_years = st.sidebar.multiselect(
    "Select Year:",
    options=year_options,
    default=year_options
)

# Apply filters using the helper function
filtered_data = helper.filter_data(data, selected_locations, selected_years)

############################################################################
# DASHBOARD DISPLAY
############################################################################

st.markdown("# Foreclosures in Louisville, KY")

# --- Top Cards ---
if not filtered_data.empty:
    metrics = helper.calculate_metrics(filtered_data)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Foreclosures", f"{metrics['total_foreclosures']:,}")
    col2.metric("Top Zip Code", metrics["popular_zip"])
    col3.metric("Peak Filing Month", metrics["popular_foreclosure_month"])
    col4.metric("Peak Sale Month", metrics["popular_sale_month"])
    col5.metric("Top Purchaser", metrics["popular_purchaser"])

    # --- Bar Chart ---
    bar_chart_fig = helper.create_bar_chart(filtered_data)
    st.plotly_chart(bar_chart_fig, use_container_width=True)

    st.divider()

    # --- Data Table ---
    st.markdown("### Foreclosure Details")
    display_df = helper.format_data_for_display(filtered_data)
    st.dataframe(display_df, use_container_width=True)

else:
    st.warning(
        "No data available for the selected filters. "
        "Please adjust your selection.")
