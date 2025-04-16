import praw
import json
import os
import time
import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
# Reddit API Credentials (loaded from .env or defaults)


# --- End Configuration ---

def process_comment_node(comment):
    """
    Recursively processes a PRAW comment object (Comment or MoreComments).
    Returns a dictionary representing the comment and its nested replies,
    or None if it's a MoreComments object that couldn't be processed (shouldn't happen with replace_more).
    """
    if isinstance(comment, praw.models.MoreComments):
        # Theoretically, replace_more(limit=None) should handle these.
        # If we encounter one, it might indicate an issue or edge case.
        print(f"  Warning: Encountered MoreComments object unexpectedly: {comment.id}")
        return None # Skip MoreComments objects if they appear

    # Check if the comment or author has been deleted
    comment_body = comment.body if hasattr(comment, 'body') else "[deleted]"
    author_name = comment.author.name if comment.author else "[deleted]"

    comment_data = {
        "id": comment.id,
        "author": author_name,
        "body": comment_body,
        "created_utc": comment.created_utc,
        "score": comment.score,
        "depth": comment.depth,
        "replies": []
    }

    # Ensure replies attribute is loaded
    if hasattr(comment, 'replies'):
        # Process replies recursively
        for reply in comment.replies:
            processed_reply = process_comment_node(reply)
            if processed_reply: # Only add if it wasn't a skipped MoreComments
                comment_data["replies"].append(processed_reply)

    return comment_data

def fetch_comments(config):
    """
    Loads submission data, fetches comments, and saves the combined data.
    """
    CLIENT_ID = config.CLIENT_ID
    CLIENT_SECRET = config.CLIENT_SECRET
    USER_AGENT = config.USER_AGENT

    INPUT_JSON_FILENAME = config.SEARCH_RESULTS_FILENAME
    OUTPUT_JSON_FILENAME = config.SUBMISSIONS_WITH_COMMENTS_FILENAME

    DELAY_BETWEEN_SUBMISSIONS = config.DELAY_BETWEEN_SUBMISSIONS # Be nice to Reddit's API
    # --- Input Validation and Setup ---
    if CLIENT_ID == "YOUR_CLIENT_ID" or CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("ERROR: Please configure Reddit API credentials in your .env file.")
        return

    if USER_AGENT == "CommentFetcher/0.1 by YourUsername":
         print("WARNING: Please update the USER_AGENT in your .env file or script.")

    if not os.path.exists(INPUT_JSON_FILENAME):
        print(f"ERROR: Input file not found: {INPUT_JSON_FILENAME}")
        return

    print(f"Loading submissions from {INPUT_JSON_FILENAME}...")
    try:
        with open(INPUT_JSON_FILENAME, 'r', encoding='utf-8') as f:
            submissions_to_process = json.load(f)
    except json.JSONDecodeError:
        print(f"ERROR: Could not decode JSON from {INPUT_JSON_FILENAME}. Is it valid?")
        return
    except Exception as e:
        print(f"ERROR: Failed to read {INPUT_JSON_FILENAME}: {e}")
        return

    if not submissions_to_process:
        print("Input file contains no submissions to process.")
        return

    print(f"Found {len(submissions_to_process)} submissions to process.")

    # --- PRAW Initialization ---
    print("Initializing Reddit connection...")
    try:
        reddit = praw.Reddit(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            user_agent=USER_AGENT,
            # read_only=True # Usually fine for fetching comments
        )
        reddit.read_only # Test connection
        print(f"Reddit connection successful (Read Only: {reddit.read_only}).")
    except Exception as e:
        print(f"ERROR: Could not connect to Reddit. Check credentials/network. Details: {e}")
        return

    # --- Main Processing Loop ---
    all_submissions_data = []
    total_submissions = len(submissions_to_process)

    for index, submission_info in enumerate(submissions_to_process):
        submission_id = submission_info.get('id')
        if not submission_id:
            print(f"Warning: Skipping entry {index+1} due to missing 'id'.")
            continue

        print(f"\nProcessing submission {index+1}/{total_submissions}: ID {submission_id} (r/{submission_info.get('subreddit', 'N/A')}) - '{submission_info.get('title', 'N/A')[:50]}...'" )

        try:
            print(f"  Fetching submission object... ID: {submission_id}")
            submission = reddit.submission(id=submission_id)

            # Crucial step: Replace MoreComments objects to get the full tree
            # This can trigger multiple API requests depending on the tree size.
            print("  Fetching and replacing 'more comments' (can take time)...")
            # set a limit upto some threshold, whats a good number and what does it mean

            submission.comments.replace_more(limit=10) # limit=None fetches all
            print("  Finished fetching comments.")

            processed_comments = []
            print("  Processing comment tree...")
            # Get the list of top-level comments
            comment_list = submission.comments.list()
            for top_level_comment in comment_list:
                 processed_comment = process_comment_node(top_level_comment)
                 if processed_comment:
                     processed_comments.append(processed_comment)

            print(f"  Processed {len(comment_list)} top-level comment threads.")

            # Combine original submission info with processed comments
            output_data = submission_info.copy() # Start with original data
            output_data['comments_tree'] = processed_comments # Add the structured comments

            all_submissions_data.append(output_data)

        except praw.exceptions.PRAWException as e:
            print(f"  ERROR: PRAW error processing submission {submission_id}: {e}")
            # Optionally add placeholder or skip
        except Exception as e:
            print(f"  ERROR: Unexpected error processing submission {submission_id}: {e}")
            # Optionally add placeholder or skip

        # Delay to avoid hitting rate limits
        print(f"  Waiting {DELAY_BETWEEN_SUBMISSIONS} seconds...")
        time.sleep(DELAY_BETWEEN_SUBMISSIONS)

    # --- Save Results ---
    print(f"\nFinished processing all submissions.")
    print(f"Saving {len(all_submissions_data)} processed submissions with comments to {OUTPUT_JSON_FILENAME}...")
    try:
        with open(OUTPUT_JSON_FILENAME, 'w', encoding='utf-8') as f:
            json.dump(all_submissions_data, f, indent=4, ensure_ascii=False)
        print(f"Successfully saved results to {OUTPUT_JSON_FILENAME}")
    except IOError as e:
        print(f"ERROR: Could not write results to file {OUTPUT_JSON_FILENAME}. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while writing JSON: {e}")

    print("\n--- Comment Fetching Script Finished --- ")
