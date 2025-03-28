# # visualization.py
# import pandas as pd
# import streamlit as st
# from typing import List, Dict, Any, Optional

# def display_match_results(founder_id: str, founder_name: str, matches: Optional[List[Dict[str, Any]]], top_n: int):
#     """Displays the ranked list of top N investor matches using Streamlit components."""

#     st.subheader(f"🏆 Top Investor Matches for {founder_name} ({founder_id})")

#     if matches is None:
#         st.error(f"Match calculation failed for founder {founder_id}.")
#         return
#     if not matches:
#         st.info(f"No suitable investor matches found for founder {founder_id} based on the criteria.")
#         return

#     # Get the top N matches
#     top_matches = matches[:top_n]
#     num_found = len(matches)
#     num_to_display = len(top_matches)

#     st.write(f"Found {num_found} potential matches. Displaying top {num_to_display}.")

#     # --- Create DataFrame for display ---
#     df_data = []
#     for i, match in enumerate(top_matches):
#         df_data.append({
#             "Rank": i + 1,
#             "Investor Name": match.get('investor_name', 'N/A'),
#            # "Type": match.get('investor_type', 'N/A'), # Optionally add type
#             "Score": match.get('score', 'N/A'),
#             "Reasoning": match.get('reasoning', 'N/A'),
#             "Investor ID": match.get('investor_id', 'N/A'), # Keep ID for reference
#         })

#     if not df_data:
#          st.warning("No matches to display in table.")
#          return

#     results_df = pd.DataFrame(df_data)

#     # --- Style and Display DataFrame ---
#     st.dataframe(
#         results_df,
#         column_config={
#             "Rank": st.column_config.NumberColumn(width="small", format="%d"),
#             "Score": st.column_config.ProgressColumn(
#                 label="Score (/100)",
#                 width="medium",
#                 format="%d",
#                 min_value=0,
#                 max_value=100,
#             ),
#             "Reasoning": st.column_config.TextColumn(width="large"),
#             "Investor Name": st.column_config.TextColumn(width="medium"),
#            # "Type": st.column_config.TextColumn(width="small"),
#             "Investor ID": st.column_config.TextColumn(width="medium")
#         },
#         hide_index=True,
#         use_container_width=True
#     )
# visualization.py
import pandas as pd
import streamlit as st
from typing import List, Dict, Any, Optional
import logging # Import logging

# Configure logging if not already configured elsewhere (optional, good practice)
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def display_match_results(founder_id: str, founder_name: str, matches: Optional[List[Dict[str, Any]]], top_n: int):
    """Displays the ranked list of top N investor matches using Streamlit components."""

    st.subheader(f"🏆 Top Investor Matches for {founder_name} ({founder_id})")

    # --- Debug: Check input 'matches' ---
    st.write("--- Debug Info ---")
    st.write(f"Received `matches`: {type(matches)}")
    if isinstance(matches, list):
        st.write(f"Number of matches received: {len(matches)}")
        if matches:
            st.write("First match item:", matches[0])
    st.write("--- End Debug Info ---")
    # --- End Debug ---


    if matches is None:
        st.error(f"Match calculation failed or returned None for founder {founder_id}.")
        return
    if not matches:
        st.info(f"No suitable investor matches found for founder {founder_id} based on the criteria.")
        return

    # Get the top N matches
    top_matches = matches[:top_n]
    num_found = len(matches)
    num_to_display = len(top_matches)

    st.write(f"Found {num_found} potential matches. Displaying top {num_to_display}.")

    # --- Create DataFrame for display ---
    df_data = []
    if top_matches: # Ensure there are matches to process
        for i, match in enumerate(top_matches):
             # Check if 'match' is a dictionary as expected
            if isinstance(match, dict):
                df_data.append({
                    "Rank": i + 1,
                    "Investor Name": match.get('investor_name', 'N/A'),
                    "Score": match.get('score'), # Get score, handle potential None later
                    "Reasoning": match.get('reasoning', 'N/A'),
                    "Investor ID": match.get('investor_id', 'N/A'),
                })
            else:
                logging.warning(f"Skipping invalid match item (not a dict): {match}")
                st.warning(f"Skipping invalid match item found: {type(match)}") # Show warning in UI

    if not df_data:
         st.warning("Could not prepare any data for the results table, even though matches were received.")
         return

    results_df = pd.DataFrame(df_data)

    # --- Debug: Check DataFrame ---
    st.write("--- Debug Info ---")
    st.write("DataFrame created:")
    st.dataframe(results_df.head()) # Show head of raw dataframe
    st.write(f"DataFrame shape: {results_df.shape}")
    st.write(f"Score column dtype: {results_df['Score'].dtype if 'Score' in results_df.columns else 'N/A'}")
    st.write("--- End Debug Info ---")
    # --- End Debug ---

    # Ensure Score column is numeric for ProgressColumn, handle potential None/NaN
    if 'Score' in results_df.columns:
         # Convert non-numeric scores (like None or errors) to NaN, then to a number (e.g., 0 or keep NaN)
         results_df['Score'] = pd.to_numeric(results_df['Score'], errors='coerce').fillna(0).astype(int)
    else:
        st.error("Could not find 'Score' column in the results data.")
        # Optionally display the raw data if score is missing
        # st.dataframe(results_df)
        return # Stop before trying to use ProgressColumn

    # --- Style and Display DataFrame ---
    try:
        st.dataframe(
            results_df,
            column_config={
                "Rank": st.column_config.NumberColumn(
                    label="🏆 Rank", # Add emoji
                    width="small",
                    format="%d"
                ),
                "Score": st.column_config.ProgressColumn(
                    label="💯 Score (/100)", # Add emoji
                    width="medium",
                    format="%d",
                    min_value=0,
                    max_value=100,
                ),
                "Reasoning": st.column_config.TextColumn(
                    label="📝 Reasoning", # Add emoji
                    width="large"
                ),
                "Investor Name": st.column_config.TextColumn(
                    label="👤 Investor Name", # Add emoji
                    width="medium"
                ),
                "Investor ID": st.column_config.TextColumn(
                    label="🆔 Investor ID",
                    width="medium"
                )
            },
            hide_index=True,
            use_container_width=True
        )
    except Exception as e:
        st.error(f"An error occurred while trying to display the results DataFrame: {e}")
        logging.error(f"Streamlit display error: {e}", exc_info=True)
        st.write("Raw Results Data:")
        st.dataframe(results_df) # Show raw data if styled display fails