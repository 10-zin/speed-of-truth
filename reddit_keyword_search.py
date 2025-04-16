import praw
import datetime
import time
import os
from collections import defaultdict
import re # Import regex for finding keyphrases
import json # Import json library

# --- End Configuration ---

def get_keyphrase_match_percentage(text, keyphrases):
    """
    Calculates the percentage of unique keyphrases found in the text.
    Performs case-insensitive matching.
    Returns a tuple: (score, list_of_matched_keywords)
    """
    if not text or not keyphrases:
        return 0.0, []

    matched_keywords = []
    found_count = 0
    # Use regex to find whole word matches for phrases
    for phrase in keyphrases:
        # Create a regex pattern for the phrase using word boundaries (\b)
        # re.escape handles any special regex characters within the phrase itself
        pattern = r'\b' + re.escape(phrase) + r'\b'
        # Search case-insensitively using re.IGNORECASE
        if re.search(pattern, text, re.IGNORECASE):
            found_count += 1
            matched_keywords.append(phrase) # Add the matched keyword to the list

    score = (found_count / len(keyphrases)) * 100 if keyphrases else 0.0
    return score, matched_keywords

def search_reddit(config):
    """
    Searches Reddit for submissions matching the criteria and ranks them.
    """
    CLIENT_ID = config.CLIENT_ID
    CLIENT_SECRET = config.CLIENT_SECRET
    USER_AGENT = config.USER_AGENT
    SCORE_THRESHOLD = config.SCORE_THRESHOLD
    START_DATE_STR = config.START_DATE_STR
    END_DATE_STR = config.END_DATE_STR
    MAX_RESULTS = config.MAX_RESULTS
    SUBREDDITS_TO_SEARCH = config.SUBREDDITS_TO_SEARCH
    KEYPHRASES = config.KEYPHRASES
    CONTENT_KEYWORDS = config.CONTENT_KEYWORDS
    OUTPUT_FILENAME = config.SEARCH_RESULTS_FILENAME
    
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("ERROR: Please replace 'YOUR_CLIENT_ID' and 'YOUR_CLIENT_SECRET' in your .env file or environment variables.")
        return

    if USER_AGENT == "KeyphraseSearcher/0.1 by YourUsername":
         print("WARNING: Please update the REDDIT_USER_AGENT in your .env file or environment variable with a unique identifier, including your Reddit username.")

    print(f"Initializing Reddit connection...")
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            # Optional: Add read_only=True if you don't need to perform actions requiring login
            # read_only=True
        )
        # Test connection
        print(f"Read Only Status: {reddit.read_only}")
        reddit.user.me() # Basic check to see if credentials work (even in read-only)
    except Exception as e:
        print(f"ERROR: Could not connect to Reddit. Check credentials and network. Details: {e}")
        return

    print(f"Searching subreddits: {', '.join(SUBREDDITS_TO_SEARCH)}")
    print(f"For posts containing any of: {', '.join(KEYPHRASES)}")
    print(f"Date range: {START_DATE_STR} to {END_DATE_STR}")

    try:
        start_timestamp = datetime.datetime.strptime(START_DATE_STR, "%Y-%m-%d").timestamp()
        end_timestamp = datetime.datetime.strptime(END_DATE_STR, "%Y-%m-%d").timestamp()
    except ValueError:
        print("ERROR: Invalid date format. Please use YYYY-MM-DD.")
        return

    if start_timestamp >= end_timestamp:
        print("ERROR: Start date must be before end date.")
        return

    # Store results per subreddit
    all_results = defaultdict(list)

    # Construct search query - combine keyphrases with OR
    search_query = ' OR '.join(f'"{phrase}"' for phrase in KEYPHRASES) # Try quoting for phrases

    print(f"Using search query: {search_query}")

    for sub_name in SUBREDDITS_TO_SEARCH:
        print(f"\n--- Searching r/{sub_name} --- ")
        # Keep track of processed submissions per subreddit to avoid duplicates within that sub's search results
        processed_submissions_this_sub = set()
        results_this_sub = [] # Temporary list for the current subreddit

        try:
            subreddit = reddit.subreddit(sub_name)
            print(f"Fetching submissions from r/{sub_name} (this might take a while)...")
            # PRAW's search limits results, might need multiple searches or Pushshift for historical data
            # Default sort is 'relevance', could also use 'new', 'top', 'comments'
            # Limit can be set, but PRAW handles pagination; we'll filter by date manually
            # Note: Reddit's native search might not guarantee finding *all* posts in a large date range.
            # For comprehensive historical searches, Pushshift API (via PSAW or requests) is often better,
            # but it has its own limitations and is a separate service.
            for submission in subreddit.search(search_query, sort='relevance', limit=None): # Fetch more initially, then filter
                # Basic duplicate check for this subreddit's search
                if submission.id in processed_submissions_this_sub:
                    continue

                # print(submission.title) # Debug print
                # print(submission.id) # Debug print

                submission_time = submission.created_utc

                # Filter by date
                if start_timestamp <= submission_time <= end_timestamp:
                    # print(submission.selftext) # Debug print
                    text_to_search = submission.title + " " + submission.selftext
                    # Get score and the list of matched keywords
                    score, matched_keywords = get_keyphrase_match_percentage(text_to_search, CONTENT_KEYWORDS)
                    # print(score) # Debug print
                    if score > SCORE_THRESHOLD: # Only include posts that actually contain at least one keyphrase
                        # Truncate selftext to first 50 words
                        # selftext_preview = ""
                        # if submission.selftext:
                        #     words = submission.selftext.split()
                        #     selftext_preview = words
                            # if len(words) > 100:
                            #     selftext_preview += "..."

                        results_this_sub.append({
                            "id": submission.id,
                            "score": score,
                            "title": submission.title,
                            "created_utc": submission.created_utc,
                            "selftext_preview": submission.selftext, # Add truncated selftext
                            "matched_keywords": matched_keywords # Add list of matched keywords
                        })
                        processed_submissions_this_sub.add(submission.id)
                        print(f"Found potential match in r/{sub_name}: ID {submission.id}, Score: {score:.2f}%" ) # Progress indicator
                        # print(submission.title) # Debug print

                # Optional: Add a small delay to be nice to Reddit's API
                time.sleep(0.1)

                # Stop if we've processed enough potential candidates even before sorting/limiting
                # This is a heuristic to avoid excessive API calls if MAX_RESULTS is small
                # if len(results_this_sub) > MAX_RESULTS * 5 and MAX_RESULTS > 0: # Check 5x needed results
                #    print("Gathered sufficient potential candidates, proceeding to sort...")
                #    break

                # Check if submission is older than start date - stop searching if sorted by 'new'
                if submission_time < start_timestamp:
                     print(f"Reached submissions older than the start date in r/{sub_name}, stopping search for this subreddit.")
                     break

            # Store results for this subreddit
            all_results[sub_name] = results_this_sub
            print(f"Found {len(results_this_sub)} posts in r/{sub_name} within the date range containing keyphrases.")

        except praw.exceptions.PRAWException as e:
            print(f"An error occurred during search in r/{sub_name}: {e}")
            print(f"Skipping subreddit r/{sub_name}...")
            continue # Move to the next subreddit
        except Exception as e:
            print(f"An unexpected error occurred during search in r/{sub_name}: {e}")
            print(f"Skipping subreddit r/{sub_name}...")
            continue # Move to the next subreddit

    print(f"\n--- Processing Complete --- ")

    # Prepare data for JSON output and keep console output limited
    final_results_for_json = []
    total_found_overall = 0

    print(f"\n--- Processing Results for JSON Output (Max {MAX_RESULTS} per Subreddit) --- ")
    if not all_results:
        print("No matching posts found in any searched subreddit.")
    else:
        for sub_name, results_list in all_results.items():
            if not results_list:
                print(f"No matching posts found in r/{sub_name}.")
                continue

            # Sort results by score (descending), then by date (descending) as a tie-breaker
            results_list.sort(key=lambda x: (x['score'], x['created_utc']), reverse=True)

            # Limit results for this subreddit
            if MAX_RESULTS > 0:
                limited_list = results_list[:MAX_RESULTS]
            else:
                limited_list = results_list

            print(f"Selected top {len(limited_list)} results from r/{sub_name} for saving.")

            # Add subreddit info to each result dictionary and add to the final list
            for result in limited_list:
                result['subreddit'] = sub_name # Add subreddit name
                # Optionally convert timestamp to readable string for JSON
                result['created_str'] = datetime.datetime.fromtimestamp(result['created_utc']).strftime('%Y-%m-%d %H:%M:%S UTC')
                final_results_for_json.append(result)
                total_found_overall += 1

        # Optional: Sort the combined list by score if you want overall ranking in the JSON
        # final_results_for_json.sort(key=lambda x: x['score'], reverse=True)

    # Write the results to a JSON file
    print(f"\nSaving {total_found_overall} results to {OUTPUT_FILENAME}...")
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(final_results_for_json, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved results to {OUTPUT_FILENAME}")
    except IOError as e:
        print(f"ERROR: Could not write results to file {OUTPUT_FILENAME}. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing JSON: {e}")

    print(f"\n--- Script Finished --- ")
    # Example URL from the first result saved (if any)
    if final_results_for_json:
        first_id = final_results_for_json[0]['id'] # Assuming sorted by subreddit, then score
        print(f"You can retrieve full post details using the IDs, e.g., https://www.reddit.com/comments/{first_id}")
    else:
        print("No results were saved.")

# if __name__ == "__main__":
#     search_reddit() 