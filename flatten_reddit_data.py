import json
from typing import List, Dict, Any
from pathlib import Path
import re

def is_relevant(comment: Dict[str, Any]) -> bool:
    score_filter = comment.get('score', 0) > 150 or comment.get('score', 0) < -10
    #  or 
    return score_filter or check_kyiv_mentioned(comment.get('body', ''))

def check_kyiv_mentioned(text: str) -> bool:
    """Check if 'Kyiv' or 'Kiev' is mentioned in the text."""
    pattern = r'\b(kyiv|kiev|kyviv)\b'
    return re.search(pattern, text, re.IGNORECASE)

def clean_text(text):
    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)
    # Remove unicode escape characters like \uXXXX
    text = re.sub(r'\\u[\dA-Fa-f]{4}', '', text)
    # Remove non-ASCII characters (optional, depending on the requirement)
    text = re.sub(r'[^\x00-\x7F]+', '', text)
    return text

def process_comment(comment: Dict[str, Any], parent_ids: List[str], parent_info: List[Dict[str, Any]], 
                   post_attributes: Dict[str, Any], flattened_items: List[Dict[str, Any]]) -> None:
    """Process a single comment and its replies recursively."""
    # Create a copy of the comment without the replies
    comment_copy = comment.copy()
    replies = comment_copy.pop('replies', [])
    
    # Add parent information
    comment_copy['parent_tree'] = {
        'parent_ids': parent_ids.copy(),
        'parent_info': parent_info.copy()
    }
    
    # Add post-level attributes
    for key, value in post_attributes.items():
        comment_copy[key] = value
    
    # Add the flattened comment to our list
    flattened_items.append(comment_copy)
    
    # Process all replies
    for reply in replies:
        # Add current comment's relevant info to parent info
        current_parent_info = {
            'id': comment['id'],
            'author': comment.get('author', '[deleted]'),
            'body': comment.get('body', '[deleted]'),
            'score': comment.get('score', 0),
            'created_utc': comment.get('created_utc'),
            'depth': comment.get('depth', 0)
        }
        reply['body'] = clean_text(reply.get('body', ''))
        process_comment(
            reply,
            parent_ids + [comment['id']],
            parent_info + [current_parent_info],
            post_attributes,
            flattened_items
        )

def process_post(post: Dict[str, Any], flattened_items: List[Dict[str, Any]]) -> None:
    """Process a single post and its comment tree."""
    # Create a copy of the post without the comments tree
    post['title'] = clean_text(post.get('title', ''))
    post['selftext_preview'] = clean_text(post.get('selftext_preview', ''))
    post_copy = post.copy()
    comments_tree = post_copy.pop('comments_tree', [])
    
    # Add empty parent tree for the main post
    post_copy['parent_tree'] = {
        'parent_ids': [],
        'parent_info': []
    }
    
    # Extract post-level attributes that should be passed to all comments
    post_attributes = {
        'subreddit': post.get('subreddit', '')
    }
    
    # Add the flattened post to our list
    flattened_items.append(post_copy)
    
    # Process all comments
    for comment in comments_tree:
        # Add post's relevant info to parent info
        if not is_relevant(comment):
            continue
        comment['body'] = clean_text(comment.get('body', ''))

        post_parent_info = {
            'id': post['id'],
            'title': post.get('title', ''),
            'score': post.get('score', 0),
            'created_utc': post.get('created_utc'),
            'selftext_preview': post.get('selftext_preview', '')
        }
        process_comment(
            comment,
            [post['id']],
            [post_parent_info],
            post_attributes,
            flattened_items
        )

def main():
    # Input and output file paths
    input_file = Path('data/reddit_submissions_with_comments.json')
    output_file = Path('data/flattened_reddit_data.json')
    
    # Read the input JSON file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Initialize our flattened items list
    flattened_items = []
    
    # Process each post
    for post in data:
        process_post(post, flattened_items)
    print(f"Flattened {len(flattened_items)} items")
    
    # Write the flattened data to a new JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(flattened_items, f, indent=4, ensure_ascii=False)

if __name__ == '__main__':
    main() 