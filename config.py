import os
from dotenv import load_dotenv # Import dotenv

# Load environment variables from .env file
load_dotenv()

class ClientConfig:
    # --- Configuration ---
    # Replace with your Reddit API credentials (loaded from .env or defaults)
    CLIENT_ID = os.getenv("CLIENT_ID", "YOUR_CLIENT_ID") # Replace default or set env var
    CLIENT_SECRET = os.getenv("CLIENT_SECRET", "YOUR_CLIENT_SECRET") # Replace default or set env var
    USER_AGENT = os.getenv("USER_AGENT", "KeyphraseSearcher/0.1 by YourUsername") # Replace default or set env var

class TrumpStagedConfig: 
    name = "trump_assassination"
    # List of keyphrases to search for (case-insensitive)
    KEYPHRASES = ["trump ear", "trump assassination ear", "trump assassination attempt", "trump blood ear", "trump bit lip"]
    # KEYPHRASES = ["trump assassination attempt staged"]
    CONTENT_KEYWORDS = ["ear", "bit", "lip", "trump", "bullet", "fake", "blood"]
    SCORE_THRESHOLD = 20
    START_DATE_STR = "2024-07-13"
    END_DATE_STR = "2025-04-14"
    MAX_RESULTS = 50
    SUBREDDITS_TO_SEARCH = ["Askpolitics", "politics", "conspiracytheories", "AnythingGoesNews", "conspiracy", "TrueUnpopularOpinion", "PoliticalOpinions", "pics", "moderatepolitics"]
    RAW_DATA_DIR = f"data/raw/{name}"
    SEARCH_RESULTS_FILENAME = f"{RAW_DATA_DIR}/reddit_search_results.json"
    # Input and Output Filenames
    SUBMISSIONS_WITH_COMMENTS_FILENAME = f"{RAW_DATA_DIR}/reddit_submissions_with_comments.json"
    # Delay between processing submissions (in seconds) to avoid rate limits
    DELAY_BETWEEN_SUBMISSIONS = 2 # Be nice to Reddit's API
    FLATTENED_DATA_FILENAME = f"{RAW_DATA_DIR}/flattened_reddit_data.json"
    PREPROCESSED_DATA_FOLDER = f"data/preprocessed/{name}"
    STAGING_CLAIMS_ANALYSIS_FILENAME = f"{PREPROCESSED_DATA_FOLDER}/staging_claims_analysis.json"
    SKIP_DELETED_PARENTS = True

class GhostOfKievConfig: 
    name = "ghost_of_kyiv"
    # List of keyphrases to search for (case-insensitive)
    KEYPHRASES = ["ghost of Kiev", "ghost of kyiv", "mig-29 legend", "stepan tarabalka" "ghost ukraine dcs footage"]
    CONTENT_KEYWORDS = ["Ukraine", "Ukrainian", "Russia", "war", "mig-29", "ghost", "kiev", "kyiv", "legend"]
    SCORE_THRESHOLD = 20
    START_DATE_STR = "2022-02-24"
    END_DATE_STR = "2025-04-14"
    MAX_RESULTS = 100
    SUBREDDITS_TO_SEARCH = ["Ukraine", "aviation", "conspiracytheories", "AnythingGoesNews", "conspiracy", "TrueUnpopularOpinion", "PoliticalOpinions", "pics", 
                        "acecombat", "europe", "UkraineWarVideoReport", "UkrainianConflict", "awfuleverything", "Project_Wingman", "WarplanePorn", "Damnthatsinteresting",
                        "TrevorHenderson", "MilitaryPorn", "memes", "RussianWarFootageV", "neoliberal", ""] # List of subreddits
    # SUBREDDITS_TO_SEARCH = ["memes", "UkraineWarVideoReport", "acecombat"]
    RAW_DATA_DIR = f"data/raw/{name}"
    SEARCH_RESULTS_FILENAME = f"{RAW_DATA_DIR}/reddit_search_results.json"
    # Input and Output Filenames
    SUBMISSIONS_WITH_COMMENTS_FILENAME = f"{RAW_DATA_DIR}/reddit_submissions_with_comments.json"
    # Delay between processing submissions (in seconds) to avoid rate limits
    DELAY_BETWEEN_SUBMISSIONS = 2 # Be nice to Reddit's API
    FLATTENED_DATA_FILENAME = f"{RAW_DATA_DIR}/flattened_reddit_data.json"
    PREPROCESSED_DATA_FOLDER = f"data/preprocessed/{name}"
    STAGING_CLAIMS_ANALYSIS_FILENAME = f"{PREPROCESSED_DATA_FOLDER}/staging_claims_analysis.json"
    SKIP_DELETED_PARENTS = True