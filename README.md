# Founder-Investor-Matcher

## Objective

This project aims to develop an AI-powered system that matches startup founders with potentially suitable investors based on structured data profiles. It leverages the Google Gemini API to analyze compatibility and generate a ranked list of matches with scores and reasoning.

## Features

*   **Data Loading:** Loads founder and investor data from structured CSV files (`founders.csv`, `investors.csv`).
*   **AI-Powered Analysis:** Utilizes the Google Gemini API (specifically `gemini-1.5-flash-latest` in the current implementation) to perform nuanced compatibility analysis between each founder-investor pair.
*   **Structured Prompting:** Employs detailed prompts instructing the AI to evaluate specific criteria (Industry Fit, Stage Fit, Funding/Check Size Fit, Geographic Focus, Qualitative Thesis Fit) and return a structured JSON response.
*   **Match Score & Reasoning:** Extracts a compatibility score (0-100) and a textual justification directly from the Gemini API's analysis.
*   **Ranked Output:** Presents the potential investor matches ranked by their compatibility score in descending order.
*   **Efficient API Usage:** Implements `asyncio` for concurrent API calls, significantly speeding up the process compared to sequential requests.
*   **Rate Limiting & Retries:** Incorporates `asyncio.Semaphore` to limit concurrent requests and includes automatic retries with exponential backoff for API rate limit errors (HTTP 429).
*   **User-Friendly Interface:** Provides a Jupyter Notebook (`.ipynb`) for easy setup, execution, and visualization of results, allowing users to specify a founder ID and get the top matches.

## Technology Stack

*   **Language:** Python 3.x
*   **Core Libraries:**
    *   `google-generativeai`: Google Gemini API Python SDK
    *   `pandas`: Data loading, manipulation, and preparation
    *   `asyncio`: Asynchronous programming for concurrent API calls
    *   `python-dotenv`: Loading API keys from `.env` files
    *   `json`: Parsing API responses
    *   `logging`: Tracking progress and errors
*   **Environment:** Jupyter Notebook / Lab (for the primary user interface)

## App Video

https://github.com/user-attachments/assets/fe43830a-02b1-44a6-b36a-203f25d4dc7b


## Setup Instructions

1.  **Clone Repository (if applicable):** If this code is in a Git repository, clone it:
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```
    Otherwise, ensure you have the Python script/notebook and CSV data files in the same directory.

2.  **Python Installation:** Ensure you have Python 3.7+ installed.

3.  **Install Dependencies:** Install the required Python libraries:
    ```bash
    pip install google-generativeai pandas python-dotenv jupyterlab notebook nest_asyncio
    ```
    *(Note: `nest_asyncio` is included for better compatibility of `asyncio` within Jupyter environments)*

4.  **Get Gemini API Key:** Obtain an API key from Google AI Studio: [https://aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

5.  **Create `.env` File:** Create a file named `.env` in the project's root directory and add your API key:
    ```
    GEMINI_API_KEY=YOUR_API_KEY_HERE
    ```
    *(Replace `YOUR_API_KEY_HERE` with your actual key)*

6.  **Prepare Data Files:** Ensure the `founders.csv` and `investors.csv` files (structured as defined during development) are present in the same directory as the notebook/script.

## Usage (Jupyter Notebook)

1.  **Launch Jupyter:** Start Jupyter Lab or Jupyter Notebook from your terminal in the project directory:
    ```bash
    jupyter lab
    # or
    jupyter notebook
    ```
2.  **Open Notebook:** Open the `.ipynb` notebook file (e.g., `founder_investor_matcher.ipynb`).
3.  **Run Setup Cells:** Execute the cells in sections 1-4 sequentially to import libraries, load the API key, define constants, load data, and define necessary functions. Ensure no errors occur, particularly during API key configuration and data loading.
4.  **Specify Founder ID:** Navigate to section "5. Execution (User-Friendly)", cell 5.2. Modify the `founder_id_to_process` variable to the specific ID of the founder (from `founders.csv`) you wish to find matches for.
5.  **Run Execution Cell:** Execute cell 5.3 ("Run the Matching and Display Results"). This will trigger the API calls and display the top 5 ranked investor matches along with their scores and the reasoning provided by the Gemini API.
6.  **Interpret Output:** Review the printed output, which shows the rank, investor name/ID, match score, and the AI's justification for that score.

## Core Approach

The matching process relies heavily on the capabilities of the large language model (LLM) provided by the Gemini API.

1.  **Data Preparation:** Founder and investor data are loaded from CSVs into pandas DataFrames. Basic cleaning (handling missing values) is performed.
2.  **Iterative Matching:** For a selected founder, the system iterates through *every* investor in the dataset.
3.  **Prompt Engineering:** For each founder-investor pair, a detailed prompt is dynamically generated (`create_match_prompt`). This prompt provides the AI with:
    *   Context (acting as a VC analyst).
    *   Structured profiles of both the founder's startup and the investor's preferences/thesis.
    *   Specific instructions to evaluate the match based on key criteria (Industry, Stage, Funding, Geography, Qualitative fit based on thesis, product, traction, USP).
    *   A strict requirement to output *only* a JSON object containing an integer `score` (0-100) and a string `reasoning`.
4.  **AI Analysis & Scoring:** The prompt is sent to the Gemini API (`get_match_analysis_async`). The API analyzes the provided text based on its training and the prompt's instructions, generating the compatibility `score` and `reasoning`. The score is therefore derived directly from the AI's assessment.
5.  **Asynchronous Execution:** To handle potentially numerous investor comparisons efficiently, API calls are made concurrently using `asyncio` and `asyncio.gather`.
6.  **Rate Limiting/Robustness:** An `asyncio.Semaphore` limits simultaneous requests to avoid hitting API rate limits. If rate limits (`429` errors) are encountered, the system automatically retries the request with an increasing delay (exponential backoff).
7.  **Result Aggregation & Ranking:** Results from the API calls are collected. Failed or malformed responses are handled gracefully. Successful results (containing a valid score) are compiled into a list.
8.  **Output:** The list of successful matches is sorted by score in descending order, and the top N (default 5) results are displayed to the user (`display_matches`).

## Suggested Improvements

1.  **Hybrid Scoring Model:** Combine the AI-generated score with rule-based scores. For instance, apply hard penalties if there's a complete mismatch in essential criteria like industry or stage, even if the AI gives a moderate qualitative score. This adds a layer of deterministic validation.
2.  **Weighted Criteria:** Modify the prompt or post-process the score to allow weighting of different criteria (e.g., make Industry Fit more important than Geographic Focus for some use cases).
3.  **Scalability - Pre-filtering:** For very large datasets, calling the LLM for every pair can be slow and expensive. Implement a pre-filtering step using:
    *   **Rule-based filtering:** Quickly eliminate investors with obvious mismatches (wrong stage, industry, location, check size range).
    *   **Vector Embeddings:** Generate embeddings for founder descriptions/USPs and investor theses. Use vector similarity search (e.g., using Faiss, Annoy, or a vector database) to find the top K most relevant investors *before* sending them to the Gemini API for detailed analysis and scoring.
4.  **Enhanced Data Input/Validation:**
    *   Implement stricter data validation on input CSVs.
    *   Consider using a database instead of CSVs for better data integrity and querying capabilities.
    *   Allow for richer data inputs (e.g., founder pitch decks, detailed team backgrounds).
5.  **User Interface (UI):** Develop a more interactive web-based UI using frameworks like Streamlit, Flask, or Django. This would allow users to upload data, select founders, view results, and potentially provide feedback without needing to run a Jupyter Notebook.
6.  **Feedback Loop:** Incorporate a mechanism for users (e.g., founders or analysts) to rate the quality of the suggested matches. This feedback could be used to:
    *   Fine-tune the prompts sent to the Gemini API.
    *   Train a separate "re-ranking" model on top of the Gemini scores.
7.  **Prompt Optimization:** Systematically experiment with different prompt structures, levels of detail, and explicit instructions to optimize the quality and consistency of the Gemini API's scores and reasoning.
8.  **Cost/Performance Optimization:** Monitor API usage costs. Experiment with different Gemini models (e.g., `gemini-pro` vs. `gemini-1.5-flash`) to balance cost, latency, and quality. Tune the `MAX_CONCURRENT_REQUESTS` based on observed performance and API limits.
9.  **Evaluation Metrics:** Define metrics to objectively measure the quality of matches (e.g., Precision@K, Recall@K), although this requires having some "ground truth" data or relying on user feedback.
10. **Security:** For production environments, manage API keys more securely using secrets management tools (like Google Secret Manager, AWS Secrets Manager, HashiCorp Vault) instead of `.env` files.
