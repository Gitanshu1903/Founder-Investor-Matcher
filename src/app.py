# streamlit_app.py
import streamlit as st
import asyncio
import logging
import pandas as pd
import nest_asyncio # Needed for running asyncio in Streamlit's environment

# Apply nest_asyncio early
nest_asyncio.apply()

import config
from data_loader import DataLoader
from gemini_client import GeminiClient
from matching_service import MatchingService
from visualization import display_match_results

# --- Page Configuration ---
st.set_page_config(
    page_title=config.APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded",
)

logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Caching ---
@st.cache_resource # Cache resource objects like clients
def get_gemini_client():
    try:
        return GeminiClient()
    except ValueError as e:
        st.error(f"Failed to initialize Gemini Client: {e}. Please check API Key in .env file.")
        return None
    except Exception as e:
        st.error(f"An unexpected error occurred initializing Gemini Client: {e}")
        return None


@st.cache_data # Cache data loading results
def load_app_data():
    data_loader = DataLoader()
    success = data_loader.load_all_data()
    if not success:
        st.error("Failed to load necessary data (Founders or Investors). Please check CSV files and logs.")
        return None, None, {} # Return empty structure
    founders_df, investors_df = data_loader.get_data()
    founder_options = data_loader.get_founder_options()
    if not founder_options:
        st.warning("No founders found in the data file.")
    return founders_df, investors_df, founder_options

# --- Main App Logic ---
st.title(config.APP_TITLE)
st.markdown("Select a founder to find potential investor matches based on AI analysis.")

# --- Load Data and Initialize Services ---
founders_df, investors_df, founder_options = load_app_data()
gemini_client = get_gemini_client()

if founders_df is not None and investors_df is not None and founder_options and gemini_client:
    matcher = MatchingService(founders_df, investors_df, gemini_client)

    # --- Sidebar ---
    st.sidebar.header("Select Founder")
    selected_founder_id = st.sidebar.selectbox(
        "Choose a Founder:",
        options=list(founder_options.keys()),
        format_func=lambda x: founder_options.get(x, "Unknown ID"),
        index=0
    )
    top_n_slider = st.sidebar.slider(
        "Number of top matches to display:",
        min_value=1,
        max_value=20,
        value=config.DEFAULT_TOP_N,
        step=1
    )
    find_matches_button = st.sidebar.button("Find Matches", type="primary")

    # --- Main Area ---
    results_placeholder = st.empty()

    if find_matches_button and selected_founder_id:
        selected_founder_name = founders_df[founders_df['startup_id'] == selected_founder_id].iloc[0].get('startup_name', selected_founder_id)

        with results_placeholder, st.spinner(f"Analyzing matches for {selected_founder_name}... Please wait."):
            try:
                matches = asyncio.run(matcher.find_matches(selected_founder_id))
            except Exception as e:
                matches = None # Ensure matches is None if async call fails
                st.error(f"An error occurred during matching API calls: {e}")
                logging.error(f"Error during matching for {selected_founder_id}: {e}", exc_info=True)

        # --- Visualization Logic Moved Here ---
        results_placeholder.empty() # Clear spinner area

        st.subheader(f"🏆 Top Investor Matches for {selected_founder_name} ({selected_founder_id})")

        # Optional Debugging (keep initially)
        st.write("--- Debug Info (Inside App) ---")
        st.write(f"Matches type: {type(matches)}")
        if isinstance(matches, list):
            st.write(f"Number of matches: {len(matches)}")
            if matches: st.write("First match:", matches[0])
        st.write("--- End Debug ---")

        if matches is None:
            # Error message already shown if exception occurred during run
            if 'e' not in locals(): # Check if error object exists from try/except
                 st.error(f"Match calculation failed or returned None for founder {selected_founder_id}.")
        elif not matches:
            st.info(f"No suitable investor matches found for founder {selected_founder_id} based on the criteria.")
        else:
            # Process and display the matches
            try:
                top_matches = matches[:top_n_slider]
                num_found = len(matches)
                num_to_display = len(top_matches)

                st.write(f"Found {num_found} potential matches. Displaying top {num_to_display}.")

                df_data = []
                if top_matches:
                    for i, match in enumerate(top_matches):
                        if isinstance(match, dict):
                            df_data.append({
                                "Rank": i + 1,
                                "Investor Name": match.get('investor_name', 'N/A'),
                                "Score": match.get('score'), # Handle None later
                                "Reasoning": match.get('reasoning', 'N/A'),
                                "Investor ID": match.get('investor_id', 'N/A'),
                            })
                        else:
                             logging.warning(f"Skipping invalid match item (not a dict): {match}")

                if not df_data:
                    st.warning("Could not prepare any data for the results table.")
                else:
                    results_df = pd.DataFrame(df_data)

                    # Clean Score column before display configuration
                    if 'Score' in results_df.columns:
                         results_df['Score'] = pd.to_numeric(results_df['Score'], errors='coerce').fillna(0).astype(int)
                    else:
                         st.error("Internal Error: 'Score' column missing in results data.")
                         st.dataframe(results_df) # Show raw data
                         st.stop() # Stop further processing if score is missing


                    # Display DataFrame using st.dataframe
                    st.dataframe(
                        results_df,
                        column_config={
                             "Rank": st.column_config.NumberColumn(label="🏆 Rank", width="small", format="%d"),
                             "Score": st.column_config.ProgressColumn(
                                label="💯 Score (/100)", width="medium", format="%d", min_value=0, max_value=100,
                             ),
                             "Reasoning": st.column_config.TextColumn(label="📝 Reasoning", width="large"),
                             "Investor Name": st.column_config.TextColumn(label="👤 Investor Name", width="medium"),
                             "Investor ID": st.column_config.TextColumn(label="🆔 Investor ID", width="medium")
                         },
                        hide_index=True,
                        use_container_width=True
                    )

            except Exception as display_e:
                st.error(f"An error occurred while displaying results: {display_e}")
                logging.error(f"Error displaying results: {display_e}", exc_info=True)
                # Optionally show raw matches list if DataFrame display fails
                st.write("Raw Matches Data:")
                st.json(matches[:top_n_slider]) # Display raw JSON if table fails


    else:
         # This message shows only if the button hasn't been pressed yet
         if not find_matches_button:
              results_placeholder.info("Select a founder and click 'Find Matches' in the sidebar.")
         # If button was pressed but selected_founder_id was somehow invalid (shouldn't happen with selectbox)
         elif find_matches_button and not selected_founder_id:
              results_placeholder.warning("Please select a valid founder.")


elif not config.API_KEY:
     st.error("GEMINI_API_KEY is not set. Please configure it in the .env file.")
else:
    st.warning("Application could not start. Please check data files and API key configuration. Check terminal/logs for specific errors during data loading.")

st.sidebar.markdown("---")
st.sidebar.info("Powered by Google Gemini & Streamlit")
