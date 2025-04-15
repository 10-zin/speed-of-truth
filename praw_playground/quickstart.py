import praw
import datetime
import time
from datetime import timezone

reddit = praw.Reddit(
    client_id="yJyqiBjYv2LhSXuIw82tYw",
    client_secret="juUXBAiNwIUBwjfEcBsoiFN3fBFE3Q",
    password="Reddit@b347",
    user_agent="USERAGENT",
    username="10zin_",
)

print(reddit.user.me())

"""
Get all reddit posts within a specific date range (July-August 2024),
including the OP post content, comments and threads.
Filtered by the keywords list.
"""

# Define keywords to filter posts
keywords = ["help", "tutorial", "guide", "error", "question"] # Adjust as needed

# Choose the subreddit to search
subreddit_name = "learnpython" # Example: "learnpython", "datascience", etc.
subreddit = reddit.subreddit(subreddit_name)

# Define the date range for filtering
start_date = datetime.datetime(2024, 7, 1, tzinfo=timezone.utc)  # July 1, 2024
end_date = datetime.datetime(2024, 8, 31, 23, 59, 59, tzinfo=timezone.utc)  # August 31, 2024

# Convert to Unix timestamps (what Reddit uses)
start_timestamp = int(start_date.timestamp())
end_timestamp = int(end_date.timestamp())

# List to store data of matched posts
matched_posts_data = []

print(f"Searching submissions in r/{subreddit.display_name} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} for keywords: {keywords}")

# Use PRAW's search functionality with time filtering
# We'll search in the subreddit with an empty query and then filter by our keywords
limit_submissions = 50  # Set a limit for testing
# The search is empty string (returns all posts) within the time range
for submission in subreddit.search('', sort='new', time_filter='all', limit=limit_submissions, 
                                syntax='lucene', after=start_timestamp, before=end_timestamp):
    # Combine title and selftext for keyword searching
    text_to_search = submission.title + " " + submission.selftext
    found_keyword = False

    # Check if any keyword is present (case-insensitive)
    for keyword in keywords:
        if keyword.lower() in text_to_search.lower():
            found_keyword = True
            break

    if found_keyword:
        # Get the submission date for confirmation
        submission_date = datetime.datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
        print(f"Match found: Post ID {submission.id} - Title: {submission.title[:60]}... - Date: {submission_date.strftime('%Y-%m-%d')}")
        
        post_info = {
            "id": submission.id,
            "title": submission.title,
            "url": submission.url,
            "selftext": submission.selftext,
            "created_utc": submission.created_utc,
            "date": submission_date.strftime("%Y-%m-%d %H:%M:%S"),
            "comments": []
        }

        # Fetch comments for the matched post
        try:
            submission.comments.replace_more(limit=5, threshold=10) # Expand comments, adjust limits as needed
            print(f"  Fetching comments for post {submission.id}...")
            comment_limit = 20 # Limit number of comments stored per post
            for comment in submission.comments.list()[:comment_limit]:
                # Ensure it's a Comment object and not MoreComments
                if isinstance(comment, praw.models.Comment):
                    post_info["comments"].append({
                        "id": comment.id,
                        "body": comment.body,
                        "author": str(comment.author), # Get author username, handle None
                        "score": comment.score
                    })
        except Exception as e:
            print(f"  Could not fetch comments for post {submission.id}: {e}")

        matched_posts_data.append(post_info)
        print(f"  Added post {submission.id} data.")

# --- Output Results ---
print(f"\n--- Search Complete ---")
print(f"Found {len(matched_posts_data)} posts matching the keywords between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')} in r/{subreddit_name}.")

# Optional: Save data to a file (JSON)
import json
with open('reddit_posts_data.json', 'w', encoding='utf-8') as f:
    json.dump(matched_posts_data, f, ensure_ascii=False, indent=4)
print("\nSaved matched post data to reddit_posts_data.json")


