# Reddit Keyword Searcher

This script searches a specified subreddit (or `all`) for posts within a given date range that mention any of a list of keyphrases. It ranks the results based on the percentage of unique keyphrases found in the post's title and body (selftext).

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Get Reddit API Credentials:**
    *   Go to [Reddit Apps](https://www.reddit.com/prefs/apps/).
    *   Scroll down and click "are you a developer? create an app...".
    *   Fill out the form:
        *   **Name:** Give your script a unique name (e.g., `MyKeywordSearcher`).
        *   Select **"script"** as the application type.
        *   **Description:** (Optional) A brief description.
        *   **About URL:** (Optional)
        *   **Redirect URI:** `http://localhost:8080` (This is often required for script types, even if not used).
    *   Click "create app".
    *   You will see your app listed. Note down the **client ID** (a string of characters under the app name) and the **client secret**.

3.  **Configure the Script:**
    *   Create a file named `.env` in the same directory as the script.
    *   Add the following lines to the `.env` file, replacing the placeholder values with your actual credentials and a descriptive user agent:
        ```dotenv
        REDDIT_CLIENT_ID='YOUR_CLIENT_ID'
        REDDIT_CLIENT_SECRET='YOUR_CLIENT_SECRET'
        # Replace YourUsername with your actual Reddit username
        REDDIT_USER_AGENT='KeyphraseSearcher/0.1 by YourUsername'
        ```
    *   **Important:** Add `.env` to your `.gitignore` file if you are using Git to prevent accidentally committing your secrets.

4.  **Customize Search Parameters:**
    *   Edit `reddit_keyword_search.py`:
        *   Update the `KEYPHRASES` list with the terms you want to search for.
        *   Set the `START_DATE_STR` and `END_DATE_STR` (YYYY-MM-DD).
        *   Set the `MAX_RESULTS` to limit the output.
        *   Change `SUBREDDIT_TO_SEARCH` if you want to search a specific subreddit instead of `all`.

## Usage

```bash
python reddit_keyword_search.py
```

The script will print the progress and finally output the ranked list of post IDs, their match scores, and creation dates.

## Notes

*   **Rate Limits:** Be mindful of Reddit's API rate limits. The script includes a commented-out `time.sleep(0.1)` which you can enable if you encounter issues.
*   **Historical Data:** Reddit's native search API (`subreddit.search`) might not be exhaustive for older posts or very large date ranges. For more comprehensive historical searches, consider using the Pushshift API (requires separate implementation, often using the `requests` library or the `psaw` wrapper).
*   **Keyphrase Matching:** The current script checks for the presence of keyphrases. The ranking is based on the *percentage* of unique keyphrases found, not the frequency of a single keyphrase.
*   **Subreddit Choice:** Searching `all` can be very time-consuming and might yield less relevant results. Searching specific, relevant subreddits is often more effective.
