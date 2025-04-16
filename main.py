import os
import argparse
from config import TrumpStagedConfig, GhostOfKievConfig
from reddit_keyword_search import search_reddit
from fetch_reddit_comments import fetch_comments
from flatten_reddit_data import flatten_reddit_data
from analyze_staging_claims import analyze_staging_claims

def main():
    parser = argparse.ArgumentParser(description='Search Reddit for keyphrases')
    parser.add_argument('--config', type=str, default='trump_staged', choices=['trump_staged', 'ghost_of_kyiv'], help='Configuration to use')
    args = parser.parse_args()

    if args.config == 'trump_staged':
        config = TrumpStagedConfig()
    elif args.config == 'ghost_of_kyiv':
        config = GhostOfKievConfig()
    else:
        raise ValueError(f"Invalid configuration: {args.config}")

    os.makedirs(config.RAW_DATA_DIR, exist_ok=True)
    os.makedirs(config.PREPROCESSED_DATA_FOLDER, exist_ok=True)
    search_reddit(config)
    fetch_comments(config)
    flatten_reddit_data(config)
    analyze_staging_claims(config)

if __name__ == '__main__':
    main()
