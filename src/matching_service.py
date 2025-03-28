# # matching_service.py
# import pandas as pd
# import asyncio
# import logging
# from typing import List, Dict, Optional, Any

# from data_loader import DataLoader
# from gemini_client import GeminiClient

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# class MatchingService:
#     """Orchestrates the founder-investor matching process."""

#     def __init__(self, data_loader: DataLoader, gemini_client: GeminiClient):
#         self.data_loader = data_loader
#         self.gemini_client = gemini_client
#         self.founders_df, self.investors_df = self.data_loader.get_data()
        

#     async def find_matches(self, founder_id: str) -> Optional[List[Dict[str, Any]]]:
#         """Finds, scores, and ranks investor matches for a given founder."""

#         if self.founders_df is None or self.investors_df is None:
#             logging.error("Data not loaded in MatchingService. Cannot find matches.")
#             return None
#         if self.investors_df.empty:
#              logging.warning("No investors loaded. Cannot perform matching.")
#              return []


#         founder_row = self.founders_df[self.founders_df['startup_id'] == founder_id]
#         if founder_row.empty:
#             logging.error(f"Founder ID {founder_id} not found.")
#             return None

#         founder_data = founder_row.iloc[0]
#         founder_name = founder_data.get('startup_name', founder_id)
#         logging.info(f"--- Starting match process for Founder: {founder_name} ({founder_id}) ---")

#         tasks = []
#         investor_map = {} # Store investor data for result assembly

#         for index, investor_data in self.investors_df.iterrows():
#             investor_id = investor_data.get('investor_id')
#             if not investor_id or str(investor_id).strip() == '':
#                  logging.warning(f"Skipping investor row {index} due to invalid ID.")
#                  continue

#             investor_id = str(investor_id)
#             investor_map[investor_id] = investor_data
#             prompt = self.gemini_client.create_match_prompt(founder_data, investor_data)
#             tasks.append(self.gemini_client.get_match_analysis(prompt, investor_id))

#         if not tasks:
#             logging.warning(f"No valid investors to match against for founder {founder_id}.")
#             return []

#         logging.info(f"Sending {len(tasks)} match requests to Gemini API...")
#         results = await asyncio.gather(*tasks)
#         logging.info("Received all Gemini responses.")

#         # Process results
#         matches = []
#         successful_analyses = 0
#         failed_analyses = 0
#         for investor_id, analysis_result in results:
#             if analysis_result and isinstance(analysis_result.get('score'), int):
#                 investor_info = investor_map.get(investor_id)
#                 if investor_info is not None:
#                     matches.append({
#                         "investor_id": investor_id,
#                         "investor_name": investor_info.get('investor_name', 'N/A'),
#                         "investor_type": investor_info.get('investor_type', 'N/A'), # Add more fields if needed
#                         "score": analysis_result['score'],
#                         "reasoning": analysis_result.get('reasoning', 'N/A')
#                     })
#                     successful_analyses += 1
#                 else:
#                     logging.error(f"Internal Error: Investor info for {investor_id} not found after successful analysis.")
#                     failed_analyses +=1
#             else:
#                 if investor_id in investor_map: # Only count failure if it was a valid investor initially
#                     logging.warning(f"Failed analysis for investor {investor_id}")
#                     failed_analyses += 1

#         logging.info(f"Match analysis summary for {founder_id}: {successful_analyses} successful, {failed_analyses} failed/skipped.")

#         # Sort matches by score descending
#         matches.sort(key=lambda x: x["score"], reverse=True)

#         return matches
# matching_service.py
import pandas as pd
import asyncio
import logging
from typing import List, Dict, Optional, Any

# Remove DataLoader import if no longer needed directly
# from data_loader import DataLoader
from gemini_client import GeminiClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MatchingService:
    """Orchestrates the founder-investor matching process."""

    # Modify __init__ to accept dataframes directly
    def __init__(self,
                 founders_df: Optional[pd.DataFrame],
                 investors_df: Optional[pd.DataFrame],
                 gemini_client: GeminiClient):
        self.founders_df = founders_df
        self.investors_df = investors_df
        self.gemini_client = gemini_client
        # Removed: self.data_loader = data_loader
        # Removed: self.founders_df, self.investors_df = self.data_loader.get_data()

    async def find_matches(self, founder_id: str) -> Optional[List[Dict[str, Any]]]:
        """Finds, scores, and ranks investor matches for a given founder."""

        # This check should now correctly reflect if data was loaded successfully earlier
        if self.founders_df is None or self.investors_df is None:
            logging.error("Data not provided to MatchingService. Cannot find matches.")
            return None
        if self.founders_df.empty:
             logging.warning("Founders DataFrame provided to MatchingService is empty.")
             # Allow proceeding? Maybe still return None or [] depending on desired behavior
             return None # Let's return None if no founders to match against
        if self.investors_df.empty:
             logging.warning("No investors provided to MatchingService. Cannot perform matching.")
             return []

        # --- Rest of the find_matches method remains the same ---
        founder_row = self.founders_df[self.founders_df['startup_id'] == founder_id]
        if founder_row.empty:
            logging.error(f"Founder ID {founder_id} not found in provided data.")
            return None

        founder_data = founder_row.iloc[0]
        founder_name = founder_data.get('startup_name', founder_id)
        logging.info(f"--- Starting match process for Founder: {founder_name} ({founder_id}) ---")

        tasks = []
        investor_map = {}

        for index, investor_data in self.investors_df.iterrows():
            investor_id = investor_data.get('investor_id')
            if not investor_id or str(investor_id).strip() == '':
                 logging.warning(f"Skipping investor row {index} due to invalid ID.")
                 continue

            investor_id = str(investor_id)
            investor_map[investor_id] = investor_data
            prompt = self.gemini_client.create_match_prompt(founder_data, investor_data)
            tasks.append(self.gemini_client.get_match_analysis(prompt, investor_id))

        if not tasks:
            logging.warning(f"No valid investors to match against for founder {founder_id}.")
            return []

        logging.info(f"Sending {len(tasks)} match requests to Gemini API...")
        results = await asyncio.gather(*tasks)
        logging.info("Received all Gemini responses.")

        # Process results (logic remains the same)
        matches = []
        successful_analyses = 0
        failed_analyses = 0
        for inv_id, analysis_result in results:
            if analysis_result and isinstance(analysis_result.get('score'), int):
                investor_info = investor_map.get(inv_id)
                if investor_info is not None:
                    matches.append({
                        "investor_id": inv_id,
                        "investor_name": investor_info.get('investor_name', 'N/A'),
                        "investor_type": investor_info.get('investor_type', 'N/A'),
                        "score": analysis_result['score'],
                        "reasoning": analysis_result.get('reasoning', 'N/A')
                    })
                    successful_analyses += 1
                else:
                    logging.error(f"Internal Error: Investor info for {inv_id} not found after successful analysis.")
                    failed_analyses +=1
            else:
                if inv_id in investor_map:
                    logging.warning(f"Failed analysis for investor {inv_id}")
                    failed_analyses += 1

        logging.info(f"Match analysis summary for {founder_id}: {successful_analyses} successful, {failed_analyses} failed/skipped.")

        matches.sort(key=lambda x: x["score"], reverse=True)
        return matches