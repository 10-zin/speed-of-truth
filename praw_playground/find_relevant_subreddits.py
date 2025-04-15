import praw
import os
import datetime
from datetime import timezone
from dotenv import load_dotenv
import re # For simple word splitting

# --- Configuration ---
# Load environment variables from .env file
load_dotenv()

# Reddit API Credentials from .env
CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
PASSWORD = os.getenv("REDDIT_PASSWORD")
USER_AGENT = os.getenv("REDDIT_USER_AGENT")
USERNAME = os.getenv("REDDIT_USERNAME")

# Check if all credentials are loaded
if not all([CLIENT_ID, CLIENT_SECRET, PASSWORD, USER_AGENT, USERNAME]):
    print("Error: Missing Reddit API credentials in .env file.")
    print("Please ensure REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_PASSWORD, REDDIT_USER_AGENT, REDDIT_USERNAME are set.")
    exit()

# Topic keywords
TOPIC_KEYWORDS = ["trump", "assassination", "staged"] # Use lowercase for consistency

# Date Range (UTC)
START_DATE = datetime.datetime(2024, 7, 1, tzinfo=timezone.utc)  # July 1, 2024
END_DATE = datetime.datetime(2024, 8, 31, 23, 59, 59, tzinfo=timezone.utc) # August 31, 2024
START_TIMESTAMP = int(START_DATE.timestamp())
END_TIMESTAMP = int(END_DATE.timestamp())

# Filtering Thresholds
KEYWORD_DENSITY_THRESHOLD_PERCENT = 5.0 # Minimum % of keywords in post + comments text
MAX_SUBREDDITS_TO_CHECK = 20          # Limit how many subreddits found by name/desc are deeply checked
MAX_POSTS_PER_SUBREDDIT = 50         # Limit posts checked per subreddit in the date range
MAX_COMMENTS_PER_POST = 50           # Limit comments fetched per post
COMMENT_REPLACE_MORE_LIMIT = 3       # Depth for expanding 'more comments' links (0 for top-level only, None for all - potentially slow)
COMMENT_REPLACE_MORE_THRESHOLD = 5   # Threshold for 'more comments' expansion

# --- Helper Functions ---
def calculate_keyword_density(text, keywords):
    """Calculates the percentage of specified keywords found in a text."""
    if not text:
        return 0.0
    
    # Simple word tokenization (lowercase, split by non-alphanumeric)
    words = re.findall(r\b\w+\b', text.lower())
    if not words:
        return 0.0

    found_keywords_count = 0
    # Use a set for faster lookup
    keyword_set = set(k.lower() for k in keywords)
    present_keywords = set()

    for word in words:
        if word in keyword_set:
             present_keywords.add(word) # Count unique keywords present

    # Density calculation: (Number of unique topic keywords found / Total number of topic keywords) * 100
    if not keyword_set:
        return 0.0 # Avoid division by zero if keyword list is empty
        
    density = (len(present_keywords) / len(keyword_set)) * 100
    return density

# --- Main Logic ---
print("Initializing PRAW...")
try:
    reddit = praw.Reddit(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        password=PASSWORD,
        user_agent=USER_AGENT,
        username=USERNAME,
    )
    print(f"Logged in as: {reddit.user.me()}")
except Exception as e:
    print(f"Error initializing PRAW or logging in: {e}")
    exit()

# 1. Find potentially relevant subreddits based on keywords in name/description
print(f"\nSearching for subreddits related to keywords: {TOPIC_KEYWORDS}...")
subreddit_query = " OR ".join(TOPIC_KEYWORDS) # Simple OR query
candidate_subreddits = []
try:
    # PRAW's search returns a generator, convert to list and limit
    search_results = list(reddit.subreddits.search(subreddit_query, limit=MAX_SUBREDDITS_TO_CHECK * 2)) # Fetch more initially to allow filtering
    
    # Filter out potentially less relevant matches if needed, or just limit
    candidate_subreddits = [sub.display_name for sub in search_results[:MAX_SUBREDDITS_TO_CHECK]]
    
    if not candidate_subreddits:
        print("No subreddits found matching the query in name/description.")
        exit()
    print(f"Found {len(candidate_subreddits)} potential candidates: {candidate_subreddits}")

except Exception as e:
    print(f"Error searching for subreddits: {e}")
    exit()

# 2. Search within candidate subreddits for posts matching date and keyword density
print(f"\nAnalyzing posts in candidate subreddits between {START_DATE.strftime('%Y-%m-%d')} and {END_DATE.strftime('%Y-%m-%d')}...")
print(f"Keyword density threshold: {KEYWORD_DENSITY_THRESHOLD_PERCENT}%")

meaningful_subreddits = set() # Use a set to store unique subreddit names

for sub_name in candidate_subreddits:
    if sub_name in meaningful_subreddits: # Skip if already found to be meaningful
        continue

    print(f"\n--- Checking r/{sub_name} ---")
    try:
        subreddit = reddit.subreddit(sub_name)
        post_found_in_subreddit = False

        # Search posts within the date range
        for submission in subreddit.search('', sort='new', time_filter='all', limit=MAX_POSTS_PER_SUBREDDIT,
                                           syntax='lucene', after=START_TIMESTAMP, before=END_TIMESTAMP):
            
            # Basic check: Does the post fall within the exact timestamp range?
            # (PRAW's search with after/before based on Pushshift index might sometimes include edge cases)
            if not (START_TIMESTAMP <= submission.created_utc <= END_TIMESTAMP):
                 continue

            print(f"  Analyzing post: {submission.id} ('{submission.title[:50]}...')")
            
            # Combine post title and body
            combined_text = submission.title + " " + submission.selftext

            # Fetch and add comments
            try:
                # Expand 'more comments' links (can be slow)
                submission.comments.replace_more(limit=COMMENT_REPLACE_MORE_LIMIT, threshold=COMMENT_REPLACE_MORE_THRESHOLD)
                comment_count = 0
                for comment in submission.comments.list():
                    if comment_count >= MAX_COMMENTS_PER_POST:
                        break
                    if isinstance(comment, praw.models.Comment):
                        combined_text += " " + comment.body
                        comment_count += 1
                print(f"    Fetched {comment_count} comments.")
            except Exception as comment_e:
                print(f"    Warning: Could not fetch comments for post {submission.id}: {comment_e}")

            # Calculate keyword density
            density = calculate_keyword_density(combined_text, TOPIC_KEYWORDS)
            print(f"    Keyword density: {density:.2f}%")

            # Check if threshold is met
            if density >= KEYWORD_DENSITY_THRESHOLD_PERCENT:
                print(f"  >>> Found relevant post {submission.id} in r/{sub_name} (Density: {density:.2f}%)")
                meaningful_subreddits.add(sub_name)
                post_found_in_subreddit = True
                break # Stop checking this subreddit once one relevant post is found

        if not post_found_in_subreddit:
             print(f"  No posts met the criteria in r/{sub_name} within the checked limit ({MAX_POSTS_PER_SUBREDDIT} posts).")

    except praw.exceptions.PRAWException as praw_e:
         print(f"  Skipping r/{sub_name} due to PRAW error: {praw_e} (Might be private, banned, or other issue)")
    except Exception as e:
        print(f"  Skipping r/{sub_name} due to unexpected error: {e}")


# --- Final Output ---
print(f"\n--- Analysis Complete ---")
if meaningful_subreddits:
    print(f"Found {len(meaningful_subreddits)} subreddits containing posts matching the criteria:")
    for sub in sorted(list(meaningful_subreddits)): # Sort for consistent output
        print(f"- r/{sub}")
else:
    print("No subreddits were found containing posts that met all criteria (date range and keyword density).")
    print("Consider adjusting keywords, date range, density threshold, or search limits.") 