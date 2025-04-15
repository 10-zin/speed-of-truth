import os
import json
import argparse
from tqdm import tqdm
from datetime import datetime, timedelta
from openai import OpenAI
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
client = OpenAI()

def filter_data_by_date_and_support(input_file: str, target_date: str, support_level: str) -> List[Dict[str, Any]]:
    """
    Filter data based on target date and support level.
    Args:
        input_file: Path to the input JSON file
        target_date: Date string in YYYY-MM-DD format
        support_level: One of 'true', 'false', or 'neutral'
    Returns:
        List of filtered comments/posts
    """
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    filtered_data = []
    target_timestamp = int(datetime.strptime(target_date, "%Y-%m-%d").timestamp())
    
    for item in data.get("analyzed_comments", []):
        # Check if the item matches the support level
        if item.get("analysis", {}).get("supports") == support_level:
            # Check if the item's timestamp is after the target date
            if item.get("created_utc", 0) >= target_timestamp:
                filtered_data.append(item)
    
    return filtered_data

def get_reasons_summary(filtered_data: List[Dict[str, Any]], claim: str, context_type: str, support_level: str) -> Dict[str, str]:
    """
    Get a summary of key reasons from filtered data using ChatGPT.
    Args:
        filtered_data: List of filtered comments/posts
        claim: The claim being analyzed
        context_type: The type of context to use for the summary
    Returns:
        Dictionary of reason headers and details
    """
    # Prepare the context for ChatGPT
    context = []
    for item in filtered_data:
        item_context = []
        if context_type == 'raw_text':
            if item.get("is_post"):
                item_context.append(f"Post Title: {item.get('title', '')}")
                item_context.append(f"Content: {item.get('selftext_preview', '')}")
            else:
                item_context.append(f"Comment: {item.get('body', '')}")
        elif context_type == 'reasoning':
            item_context.append(f"Analysis: {item.get('analysis', {}).get('reasoning', '')}")
        context.append("\n".join(item_context))
    
    context_str = "\n---\n".join(context)
    
    context_type_description = {
        'raw_text': 'Reddit comments and posts',
        'reasoning': 'analysis of Reddit comments and posts'
    }

    assert support_level in ['true', 'false']
    support_level_description = {
        'true': 'support',
        'false': 'refute',
    }

    context_type_str = context_type_description[context_type]
    support_str = support_level_description[support_level]

    prompt = f"""Please summarize the following {context_type_str} that {support_str}s the claim: "{claim}"

Here are the relevant {context_type_str}:

{context_str}

Please provide a summary of the key reasons that {support_str}s the claim: "{claim}". 
Format your response as a JSON object where each key is a reason header and the value is a brief explanation.
Focus on identifying distinct patterns or themes in the reasoning.

Response format:
{{
    "Reason Header 1": "Brief explanation of this reason",
    "Reason Header 2": "Brief explanation of this reason",
    ...
}}"""
    print(prompt)
    1/0
    try:
        response = client.responses.create(
            model="gpt-4o",
            input = prompt,
            instructions = f"You are an objective analyst tasked with summarizing key reasons from {context_type_str} for {support_str}ing the claim: '{claim}'.",
            text={
                "format": {
                    "type": "json_schema",
                    "name": "support_analysis_explained",
                    "schema": {
                        "type": "object",
                        "description": f"A list of compiled reasons that {support_str}s the claim: '{claim}'. Each key is a short reason header, and each value is a short explanation.",
                        "additionalProperties": {
                            "type": "string"
                        }
                    },
                    "strict": True
                }
            }
        )
        
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error getting summary from ChatGPT: {str(e)}")
        return {}
    



def get_date_list(date_range_str: str) -> List[str]:
    # Split and parse the start and end dates
    start_str, end_str = map(str.strip, date_range_str.split('to'))
    start_date = datetime.strptime(start_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_str, "%Y-%m-%d")

    # Generate list of date strings
    date_list = [
        (start_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range((end_date - start_date).days + 1)
    ]
    return date_list

def summarize_reasons(args: argparse.Namespace):
    filtered_data = filter_data_by_date_and_support(args.input, args.date, args.support)
    
    # Get summary of reasons
    summary = get_reasons_summary(filtered_data, args.claim)
    
    # Save results
    output_data = {
        "date_filter": args.date,
        "support_level": args.support,
        "total_filtered": len(filtered_data),
        "summary": summary,
        "filtered_data": filtered_data,
    }
    
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)

def main():
    parser = argparse.ArgumentParser(description='Filter Reddit data and summarize key reasons.')
    parser.add_argument('--input', required=True, default='data/preprocessed/trump_assassination/staging_claims_analysis.json',
                      help='Input JSON file path containing analyzed comments')
    parser.add_argument('--results_dir', required=True, default='results',
                      help='Results folder for the summary')
    parser.add_argument('--dates', required=True, default='2024-07-13 to 2024-08-13',
                      help='Target date in YYYY-MM-DD format')
    parser.add_argument('--support', required=True, choices=['true', 'false', 'neutral'],
                      help='Support level to filter by')
    parser.add_argument('--claim_type', required=True, default="trump_assassination",
                      help='The claim being analyzed')
    parser.add_argument('--context_type', required=True, default="reasoning",
                      help='Type of context to use for the summary')
    
    args = parser.parse_args()

    claims = {
        "trump_assassination": "Trump's assassination attempt was staged.",
    }
    args.claim = claims[args.claim_type]
    args.output_dir = os.path.join(args.output_dir, args.claim_type, args.context_type, args.support)
    os.makedirs(args.output_dir, exist_ok=True)
    dates = get_date_list(args.dates)
    for date in tqdm(dates):
        args.date = date
        args.output = os.path.join(args.output_dir, f'{args.date}.json')
        # Filter the data
        summarize_reasons(args)

if __name__ == "__main__":
    main() 