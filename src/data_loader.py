# data_loader.py
import pandas as pd
import logging
from typing import Optional, Tuple

from config import FOUNDERS_FILE, INVESTORS_FILE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DataLoader:
    """Handles loading and basic validation of founder and investor data."""

    def __init__(self, founders_path: str = FOUNDERS_FILE, investors_path: str = INVESTORS_FILE):
        self.founders_path = founders_path
        self.investors_path = investors_path
        self.founders_df: Optional[pd.DataFrame] = None
        self.investors_df: Optional[pd.DataFrame] = None

    def _load_single_file(self, filepath: str, id_column: str) -> Optional[pd.DataFrame]:
        """Loads and cleans data from a single CSV file."""
        try:
            df = pd.read_csv(filepath, dtype={id_column: str})
            logging.info(f"Successfully loaded data from {filepath}")

            if id_column not in df.columns:
                logging.error(f"Error: ID column '{id_column}' not found in {filepath}")
                return None

            original_count = len(df)
            df.dropna(subset=[id_column], inplace=True)
            df = df[df[id_column].str.strip() != '']
            dropped_count = original_count - len(df)
            if dropped_count > 0:
                logging.warning(f"Dropped {dropped_count} rows from {filepath} due to missing/empty '{id_column}'.")

            if df.empty:
                logging.warning(f"DataFrame is empty after cleaning IDs from {filepath}.")
                return df # Return empty DF, not None

            for col in df.columns:
                if col == id_column: continue
                if df[col].dtype == 'object':
                    df[col] = df[col].fillna('').astype(str)
                elif pd.api.types.is_numeric_dtype(df[col]):
                    df[col] = df[col].fillna(0)

            df[id_column] = df[id_column].astype(str)
            return df

        except FileNotFoundError:
            logging.error(f"Error: File not found at {filepath}")
            return None
        except Exception as e:
            logging.error(f"Error loading or processing data from {filepath}: {e}")
            return None

    def load_all_data(self) -> bool:
        """Loads both founders and investors data. Returns True on success."""
        self.founders_df = self._load_single_file(self.founders_path, 'startup_id')
        self.investors_df = self._load_single_file(self.investors_path, 'investor_id')

        if self.founders_df is None or self.investors_df is None:
            logging.error("Failed to load one or both data files.")
            return False
        if self.founders_df.empty:
             logging.warning("Founders data is empty after loading.")
             # Allow proceeding if investors loaded, maybe user wants info?
        if self.investors_df.empty:
             logging.warning("Investors data is empty after loading.")
             # Allow proceeding if founders loaded? Decide based on app logic.
             # For matching, both are needed, so maybe return False here too.
             # Let's return False if investors are empty as we match *against* them.
             return False
        
        logging.info("Successfully loaded and validated both datasets.")
        return True

    def get_data(self) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame]]:
        """Returns the loaded DataFrames."""
        return self.founders_df, self.investors_df

    # def get_founder_options(self) -> dict:
    #     """Returns a dictionary of founder IDs to names for dropdowns."""
    #     if self.founders_df is not None and not self.founders_df.empty:
    #          # Create "Name (ID)" format for better display
    #          return pd.Series(
    #              self.founders_df.startup_name + " (" + self.founders_df.startup_id + ")",
    #              index=self.founders_df.startup_id
    #          ).sort_index().to_dict()
    #     return {}
    def get_founder_options(self) -> dict:
        """Returns a dictionary of founder IDs to display names for dropdowns."""
        options = {}
        if self.founders_df is not None and not self.founders_df.empty:
            for index, row in self.founders_df.iterrows():
                # Ensure both name and id are valid strings before creating the label
                f_id = str(row.get('startup_id', '')).strip()
                f_name = str(row.get('startup_name', '')).strip()

                if not f_id: # Skip if ID is missing/empty
                    continue

                # If name is missing, use the ID as the name for the label
                display_name = f_name if f_name else f"Founder ID: {f_id}"
                label = f"{display_name} ({f_id})"
                options[f_id] = label
            # Sort options by the display label (alphabetical order)
            options = dict(sorted(options.items(), key=lambda item: item[1]))
        if not options:
            logging.warning("No valid founder options generated. Check founders.csv for 'startup_id' and 'startup_name'.")
        return options
