from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import logging
from datetime import datetime
import os
import argparse
import time

# Setup logging
logging.basicConfig(
    filename='error_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Command line argument setup
def get_args():
    parser = argparse.ArgumentParser(description='Search YouTube Videos')
    parser.add_argument('query', help='Search query term')
    parser.add_argument('--max_results', type=int, default=5, help='Maximum number of results to return')
    parser.add_argument('--duration', choices=['short', 'medium', 'long'], default='medium', help='Duration of videos')
    parser.add_argument('--region', default='US', help='Region code for search results')
    return parser.parse_args()

# Get the API key from the environment variables
api_key = os.getenv('YOUTUBE_API_KEY')
if not api_key:
    raise ValueError("API key is not set in environment variables")

youtube = build('youtube', 'v3', developerKey=api_key, cache_discovery=False)

# Load existing data from a file
def load_existing_data(filepath):
    try:
        with open(filepath, "r") as file:
            data = file.read()
            if not data:  # Checks if the file is empty
                return []
            return json.loads(data)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        return []

# Save new data to a file
def save_data(filepath, new_data):
    existing_data = load_existing_data(filepath)
    if any(query.get('Search Query') == new_data.get('Search Query') for query in existing_data):
        logging.info(f"Search query '{new_data.get('Search Query')}' already exists.")
        return
    existing_data.append(new_data)
    with open(filepath, "w") as file:
        json.dump(existing_data, file, indent=2)

# Format video data
def format_video_data(item):
    video_data = item['snippet']
    video_id = item['id']['videoId']
    return {
        'channel_name': video_data['channelTitle'],  # 'channelTitle' is the key for channel name
        'video_title': video_data['title'],  # 'title' is the key for video title
        'video_id': video_id,  # 'videoId' is the key for video ID
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Formatted timestamp
        'playlist_id': item['id']['playlistId'] if 'playlistId' in item['id'] else None, # 'playlistId' is the key for playlist ID
        'url': f'https://www.youtube.com/watch?v={video_id}'  # Constructing the URL
    }

# Safe API call function with retries
def safe_api_call(call, max_retries=3):
    for _ in range(max_retries):
        try:
            return call()
        except HttpError as e:
            if e.resp.status in [403, 429]:
                time.sleep(10) 
            else:
                raise
    return None

# Search YouTube videos
def search_youtube(query, max_results):
    def api_call():
        return youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=max_results,
            type='video'
        ).execute()

    search_response = safe_api_call(api_call)
    if not search_response:
        logging.error("API call failed after retries")
        return

    videos = [format_video_data(item) for item in search_response.get('items', [])]
    if not videos:
        logging.info(f"No valid videos found for query: {query}")
        return

    data = {
        'Search Query': query,
        'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Formatted timestamp
        'Videos': videos
    }
    save_data('youtube_videos.json', data)

# Main function
def main():
    args = get_args()
    search_youtube(args.query, args.max_results)

if __name__ == "__main__":
    main()