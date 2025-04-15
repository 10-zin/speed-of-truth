import json

# Define file paths
staging_analysis_file = 'data/staging_claims_analysis.json'
flattened_data_file = 'data/flattened_reddit_data.json'
output_file = 'data/flattened_reddit_data_skipped.json'

try:
    # Load skipped comment IDs
    with open(staging_analysis_file, 'r') as f:
        staging_data = json.load(f)
    # Assuming skipped_comments is a list of dicts, e.g., [{'id': 'id1'}, {'id': 'id2'}]
    skipped_ids = [item['comment_id'] for item in staging_data.get('skipped_comments', [])]
    #find duplicates in skipped_ids count them, and remove them
    duplicates = [id for id in skipped_ids if skipped_ids.count(id) > 1]
    print(len(duplicates), f"duplicates first 10: {duplicates[0:10]}")
    skipped_ids = [id for id in skipped_ids if id not in duplicates]

    print(f"Loaded {len(skipped_ids)} skipped comment IDs.")

    # Load flattened Reddit data
    with open(flattened_data_file, 'r') as f:
        reddit_data = json.load(f)
    print(f"Loaded {len(reddit_data)} entries from {flattened_data_file}.")

    # Filter data based on skipped IDs
    # Assuming reddit_data is a dictionary {id: data_item}
    skipped_data = [element for element in reddit_data if element["id"] in skipped_ids]
    print(f"Found {len(skipped_data)} matching entries.")

    # Write the filtered data to the output file
    with open(output_file, 'w') as f:
        json.dump(skipped_data, f, indent=2)
    print(f"Successfully wrote {len(skipped_data)} entries to {output_file}.")

except FileNotFoundError as e:
    print(f"Error: File not found - {e.filename}")
except json.JSONDecodeError as e:
    print(f"Error decoding JSON: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}") 