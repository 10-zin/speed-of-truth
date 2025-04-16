import os
import json
import argparse
from openai import OpenAI
from typing import Dict, List, Any, Tuple
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI()


def is_deleted_content(text: str) -> bool:
    """
    Check if the content is deleted, removed, or empty.
    Returns True if the content is:
    - None
    - Empty string or only whitespace
    - '[deleted]' or '[removed]'
    """
    if text is None:
        return True
    text = text.strip()
    if not text:  # Empty or whitespace only
        return True
    return text.lower() in ['[deleted]', '[removed]']

def should_skip_comment(comment: Dict[str, Any], skip_with_deleted_parents: bool) -> Tuple[bool, str]:
    """
    Determine if a comment should be skipped based on deletion status or empty content.
    Returns a tuple of (should_skip: bool, reason: str)
    """
    # Check if the current comment exists and has content
    is_post = "title" in comment
    if is_post:
        if is_deleted_content(comment.get('title', '')):
            return True, "Post title is empty, deleted, or removed"
        else:
            return False, ""

    if 'body' not in comment:
        return True, "Comment has no body field"
    if is_deleted_content(comment.get('body', '')):
        return True, "Comment body is empty, deleted, or removed"
    
    # If we're checking parent tree and it exists
    if skip_with_deleted_parents and "parent_tree" in comment and "parent_info" in comment["parent_tree"]:
        for parent in comment["parent_tree"]["parent_info"]:
            # Check title and selftext for posts
            if "title" in parent:
                if is_deleted_content(parent.get("title", "")):
                    return True, "Parent post title is empty, deleted, or removed"
                if "selftext_preview" in parent and is_deleted_content(parent.get("selftext_preview", "")):
                    return True, "Parent post content is empty, deleted, or removed"
            # Check body for comments
            if "body" in parent and is_deleted_content(parent.get("body", "")):
                return True, "Parent comment is empty, deleted, or removed"
    
    return False, ""

def construct_conversation_context(comment: Dict[str, Any]) -> str:
    """
    Constructs the conversation context from a comment and its parent information.
    """
    context = []
    
    # Add parent information if available
    if "parent_tree" in comment and "parent_info" in comment["parent_tree"]:
        for parent in comment["parent_tree"]["parent_info"]:
            if "title" in parent:
                context.append(f"Post Title: {parent['title']}")
                if "selftext_preview" in parent:
                    context.append(f"Post content: {parent['selftext_preview']}")
            if "body" in parent:
                author = parent.get("author", "Unknown")
                context.append(f"Comment by {author}: {parent['body']}")
    
    # Add the current comment
    if "body" in comment:
        author = comment.get("author", "Unknown")
        context.append(f"Last Comment by {author}: {comment['body']}")
    elif "title" in comment:
        author = comment.get("author", "Unknown")
        context.append(f"Post Title: {comment['title']}")
        context.append(f"Post content: {comment['selftext_preview']}")
    
    return "\n\n".join(context)

def analyze_staging_claim(conversation_context: str) -> Dict[str, Any]:
    """
    Analyzes the conversation using GPT-4 to determine if it supports the staging claim.
    """
    mode = "last comment" if "Last Comment by" in conversation_context else "post"
#     if mode == "last comment":
#         introduction = 'Please analyze the following Reddit conversation about Trump\'s assassination attempt and determine if the last comment supports or refutes the claim that "Trump\'s assassination attempt was staged", or if it\'s neutral.'
#     else:
#         introduction = 'Please analyze the following Reddit post and determine if the post supports or refutes the claim that "Trump\'s assassination attempt was staged", or if it\'s neutral.'
#     header = f"Conversation:" if mode == "last comment" else f"Post:"
#     prompt = f"""{introduction}

# {header}
# {conversation_context}

# Please provide your analysis in JSON format with the following fields:
# - supports: boolean (true if the {mode} supports the claim that "Trump\'s assassination attempt was staged", false if it refutes it, neutral if it does not confirm or deny the claim)
# - confidence: float (0-1, how confident are you in this assessment)
# - reasoning: string (very brief explanation of your assessment)

# Response format:
# {{
#     "supports": true/false/neutral,
#     "confidence": 0.X,
#     "reasoning": "explanation"
# }}"""
    if mode == "last comment":
        introduction = 'Please analyze the following Reddit conversation about the Ghost of Kyiv and determine if the last comment supports or refutes the claim that "The story of the Ghost of Kyiv is real.", or if it\'s neutral.'
    else:
        introduction = 'Please analyze the following Reddit post and determine if the post supports or refutes the claim that "The story of the Ghost of Kyiv is real.", or if it\'s neutral.'
    header = f"Conversation:" if mode == "last comment" else f"Post:"
    prompt = f"""{introduction}

{header}
{conversation_context}

Please provide your analysis in JSON format with the following fields:
- supports: boolean (true if the {mode} supports the claim that "The story of the Ghost of Kyiv is real.", false if it refutes it, neutral if it does not confirm or deny the claim)
- confidence: float (0-1, how confident are you in this assessment)
- reasoning: string (very brief explanation of your assessment)

Response format:
{{
    "supports": true/false/neutral,
    "confidence": 0.X,
    "reasoning": "explanation"
}}"""


    

    try:
        response = client.responses.create(
        model = "gpt-4o",
        input = prompt,
        instructions = "You are an objective analyst tasked with determining if comments support or refute claims.",
        text={
            "format": {
                "type": "json_schema",
                "name": "support_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "supports": {
                            "type": "string",
                            "enum": ["true", "false", "neutral"]
                        },
                        "confidence": {
                            "type": "number",
                            # "minimum": 0,
                            # "maximum": 1
                        },
                        "reasoning": {
                            "type": "string"
                        }
                        },
                    "required": ["supports", "confidence", "reasoning"],
                    "additionalProperties": False
                    },
                "strict": True
                }
            }
        )
        return json.loads(response.output_text)
    except json.JSONDecodeError:
        return {
            "supports_staging": None,
            "confidence": 0,
            "reasoning": "Error parsing GPT-4 response"
        }

def process_reddit_data(config):
    """
    Process the Reddit data file and analyze each comment.
    """
    input_file = config.FLATTENED_DATA_FILENAME
    output_file = config.STAGING_CLAIMS_ANALYSIS_FILENAME
    skip_with_deleted_parents = config.SKIP_DELETED_PARENTS
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    results = []
    skipped_comments = []
    
    for item in tqdm(data):
        if isinstance(item, dict):
            # Check if we should skip this comment
            should_skip, skip_reason = should_skip_comment(item, skip_with_deleted_parents)
            
            if should_skip:
                skipped_comments.append({
                    "comment_id": item.get("id"),
                    "author": item.get("author"),
                    "reason": skip_reason
                })
                continue
                
            context = construct_conversation_context(item)
            analysis = analyze_staging_claim(context)
            if "body" in item:
                results.append({
                    "id": item.get("id"),
                    "is_post": False,
                    "author": item.get("author"),
                    "body": item.get("body"),
                    "created_utc": item.get("created_utc"),
                    "analysis": analysis
                })
            elif "selftext_preview" in item:
                results.append({
                    "id": item.get("id"),
                    "is_post": True,
                    "author": item.get("author"),
                    "title": item.get("title"),
                    "selftext_preview": item.get("selftext_preview"),
                    "created_utc": item.get("created_utc"),
                    "analysis": analysis
                })
    
        # Save results and skipped comments
        output_data = {
            "analyzed_comments": results,
            "skipped_comments": skipped_comments,
            "statistics": {
                "total_comments": len(data),
                "analyzed_count": len(results),
                "skipped_count": len(skipped_comments)
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)