from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import json
import logging
from datetime import datetime

# Setup logging with file name and line number
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',  # Custom date format
                    handlers=[
                        logging.FileHandler("error_log.log"),
                        logging.StreamHandler()
                    ])

# Your API Key and YouTube API service name and version
api_key = 'AIzaSyC7vmoM4nmnCaKPgGuFArBTt-fmafNjS98'
youtube = build('youtube', 'v3', developerKey=api_key, cache_discovery=False)

def load_existing_data(filepath):
    try:
        with open(filepath, "r") as file:
            data = file.read()
            if not data:  # Check if the file is empty
                return []
            return json.loads(data)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error in {filepath}: {str(e)}")
        return []  # Return empty list if the file is corrupted

def save_data(filepath, new_data):
    existing_data = load_existing_data(filepath)
    # Check if the query already exists
    if any(query['Search Query'] == new_data['Search Query'] for query in existing_data):
        logging.info(f"Search query '{new_data['Search Query']}' already exists.")
        return
    existing_data.append(new_data)
    with open(filepath, "w") as file:
        json.dump(existing_data, file, indent=2)

def youtube_search(query, max_results=5):
    try:
        search_response = youtube.search().list(
            q=query,
            part='id,snippet',
            maxResults=max_results,
            type='video'
        ).execute()
    except HttpError as e:
        logging.error(f"HTTP error occurred: {e.resp.status} - {e}")
        return
    except Exception as e:
        logging.error(f"Unexpected error occurred: {e}")
        return

    videos = []
    # Check if 'items' is present in the response
    if 'items' not in search_response:
        logging.error(f"No 'items' in search response: {search_response}")
        return

    # Extracting information from each video result
    for search_result in search_response['items']:
        if 'snippet' not in search_result or 'id' not in search_result:
            logging.error(f"Missing 'snippet' or 'id' in search_result: {search_result}")
            continue

        video_data = search_result['snippet']
        id_info = search_result['id']

        # Validate expected types and contents
        if not isinstance(video_data, dict) or not isinstance(id_info, dict):
            logging.error(f"Expected dict for 'snippet' and 'id'. Got {type(video_data)} and {type(id_info)}")
            continue

        video_id = id_info.get('videoId', None)
        if not video_id:
            logging.error(f"No 'videoId' found in 'id' field: {id_info}")
            continue

        video = {
            'Video Name': video_data.get('title', 'Unknown title'),
            'Channel Creator Name': video_data.get('channelTitle', 'Unknown channel'),
            'Date Added to YouTube': video_data.get('publishedAt', 'Unknown date').split('T')[0],
            'Video ID': video_id,
            'Link to the Video': f"https://www.youtube.com/watch?v={video_id}"
        }
        videos.append(video)

    if not videos:
        logging.info(f"No valid videos found for query: {query}")
        return

    # Create a dictionary to hold the search query and the videos with a timestamp
    data = {
        'Search Query': query,
        'Timestamp': datetime.now().isoformat(),
        'Videos': videos
    }

    # Save the data
    save_data('youtube_videos.json', data)

def main():
    try:
        youtube_search("networkchuck windows server")
    except Exception as e:
        logging.error(f"Failed to complete search due to an unexpected error: {e}")

if __name__ == "__main__":
    main()


