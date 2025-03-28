# gemini_client.py
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import asyncio
import json
import logging
from typing import Dict, Tuple, Optional, Any
import pandas as pd

import config

logging.basicConfig(level=config.LOG_LEVEL, format='%(asctime)s - %(levelname)s - %(message)s')

class GeminiClient:
    """Handles configuration and interaction with the Google Gemini API."""

    def __init__(self):
        if not config.API_KEY:
            raise ValueError("Gemini API Key not found in environment/config.")
        try:
            genai.configure(api_key=config.API_KEY)
            self.model = genai.GenerativeModel(config.GENERATIVE_MODEL_NAME)
            self.semaphore = asyncio.Semaphore(config.MAX_CONCURRENT_REQUESTS)
            logging.info(f"GeminiClient initialized with model: {config.GENERATIVE_MODEL_NAME}")
        except Exception as e:
            logging.error(f"Failed to configure Gemini API: {e}")
            raise

    def create_match_prompt(self, founder_data: pd.Series, investor_data: pd.Series) -> str:
        """Creates the detailed prompt for evaluating a founder-investor pair."""
        # (This prompt generation logic is copied directly from the previous version)
        investor_industries = ", ".join(investor_data.get('preferred_industries', '').split('|'))
        investor_stages = ", ".join(investor_data.get('preferred_stages', '').split('|'))
        founder_industries = ", ".join(founder_data.get('industry', '').split('|'))
        founder_business_models = ", ".join(founder_data.get('business_model', '').split('|'))

        prompt = f"""
        Analyze the compatibility between the following Startup Founder and Investor. Provide a match score from 0 to 100 and a brief justification.

        **Context:** You are an expert Venture Capital analyst specialized in matching startups with the right investors.

        **Startup Founder Profile:**
        - Name: {founder_data.get('startup_name', 'N/A')}
        - Industry: {founder_industries}
        - Stage: {founder_data.get('startup_stage', 'N/A')}
        - Funding Required (USD): ${founder_data.get('funding_required_usd', 0):,}
        - Location: {founder_data.get('location_city', 'N/A')}, {founder_data.get('location_country', 'N/A')}
        - Business Model: {founder_business_models}
        - MRR (USD): ${founder_data.get('mrr_usd', 0):,}
        - User Count: {founder_data.get('user_count', 0)}
        - Team Size: {founder_data.get('team_size', 'N/A')}
        - Product Description: {founder_data.get('product_description', 'N/A')}
        - Unique Selling Proposition (USP): {founder_data.get('usp', 'N/A')}
        - Traction Summary: {founder_data.get('traction_summary', 'N/A')}

        **Investor Profile:**
        - Name: {investor_data.get('investor_name', 'N/A')} ({investor_data.get('investor_type', 'N/A')})
        - Preferred Industries: {investor_industries}
        - Investment Range (USD): ${investor_data.get('min_investment_usd', 0):,} - ${investor_data.get('max_investment_usd', 0):,}
        - Average Check Size (USD): ${investor_data.get('check_size_avg_usd', 0):,}
        - Preferred Stages: {investor_stages}
        - Geographic Focus: {investor_data.get('geographic_focus', 'N/A')}
        - Investment Thesis: {investor_data.get('investment_thesis', 'N/A')}
        - Example Portfolio Companies: {investor_data.get('portfolio_companies', 'N/A')}

        **Task:**
        Evaluate the match based on the following criteria:
        1.  Industry Fit: Does the startup's industry align with the investor's preferences?
        2.  Stage Fit: Does the startup's current stage match the investor's preferred investment stages?
        3.  Funding/Check Size Fit: Is the startup's required funding within the investor's typical investment range or average check size?
        4.  Geographic Focus: Does the startup's location align with the investor's geographic preferences?
        5.  Qualitative Fit: Consider the alignment between the startup's product, traction, USP, and business model with the investor's thesis and past investments. Is there a strategic or thesis-driven reason for this investor to be interested?

        **Output Format:**
        Return your response ONLY as a JSON object with the following structure:
        {{
          "score": <integer between 0 and 100>,
          "reasoning": "<string explaining the score based on the criteria>"
        }}

        **Scoring Guidance:**
        - 85-100: Excellent fit across most key criteria, strong qualitative alignment.
        - 70-84: Good fit, alignment on major criteria (e.g., industry, stage), reasonable qualitative fit.
        - 50-69: Partial fit, alignment on some criteria but mismatches on others (e.g., stage or check size slightly off, thesis alignment is okay but not perfect).
        - 25-49: Weak fit, significant mismatches in core criteria (e.g., wrong industry, wrong stage).
        - 0-24: Poor fit, fundamental mismatches across most criteria.

        Now, provide the JSON output for the match between {founder_data.get('startup_name', 'this startup')} and {investor_data.get('investor_name', 'this investor')}.
        """
        return prompt


    async def get_match_analysis(self, prompt: str, investor_id: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """
        Calls the Gemini API asynchronously, respecting semaphore and retries.
        Returns the investor_id and the parsed JSON response or None on failure.
        """
        retries = config.RETRY_ATTEMPTS
        delay = float(config.INITIAL_RETRY_DELAY_SECONDS)
        last_exception = None

        async with self.semaphore: # Acquire semaphore
            for attempt in range(retries + 1):
                try:
                    await asyncio.sleep(0.1 * attempt) # Small stagger delay
                    logging.debug(f"API Call Attempt {attempt+1}/{retries+1} for investor {investor_id}")
                    response = await self.model.generate_content_async(prompt)

                    if not response.parts:
                         try: # Check for safety blocks
                            if response.prompt_feedback.block_reason:
                                logging.warning(f"Request for investor {investor_id} blocked. Reason: {response.prompt_feedback.block_reason}")
                                return investor_id, None
                         except Exception: pass # Ignore if feedback structure absent
                         logging.warning(f"Empty response for investor {investor_id} (Attempt {attempt+1}).")
                         return investor_id, None # Don't retry empty

                    raw_text = response.text
                    if raw_text.strip().startswith("```json"):
                        raw_text = raw_text.strip()[7:-3].strip()
                    elif raw_text.strip().startswith("```"):
                        raw_text = raw_text.strip()[3:-3].strip()

                    try:
                        match_data = json.loads(raw_text)
                        if isinstance(match_data, dict) and "score" in match_data and "reasoning" in match_data and isinstance(match_data['score'], int):
                            logging.info(f"Success for investor {investor_id} (Attempt {attempt+1})")
                            return investor_id, match_data
                        else:
                            logging.warning(f"Malformed JSON structure for investor {investor_id}. Data: {match_data}")
                            return investor_id, None
                    except json.JSONDecodeError:
                        logging.error(f"JSON Decode Error for investor {investor_id}. Raw: {raw_text}")
                        return investor_id, None

                except google_exceptions.ResourceExhausted as e:
                    last_exception = e
                    if attempt < retries:
                        logging.warning(f"Rate limit (429) for investor {investor_id} (Attempt {attempt+1}). Retrying in {delay:.2f}s...")
                        await asyncio.sleep(delay)
                        delay *= 2 # Exponential backoff
                    else:
                        logging.error(f"Rate limit (429) for investor {investor_id}. Max retries exceeded.")
                    continue # Next attempt or finish loop

                except Exception as e:
                    last_exception = e
                    logging.error(f"API Error for investor {investor_id} (Attempt {attempt+1}): {type(e).__name__} - {e}")
                    break # Break on non-429 errors

            logging.error(f"Failed API call for investor {investor_id} after {retries+1} attempts. Last error: {last_exception or 'Unknown'}")
            return investor_id, None