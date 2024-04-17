import json
import logging
from youtube_transcript_api import YouTubeTranscriptApi

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    handlers=[
                        logging.FileHandler("error_log.log"),
                        logging.StreamHandler()
                    ])

def load_existing_data(filepath):
    """ Load existing data from JSON file, return an empty list if not found or empty. """
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

def video_already_exists(video_id, existing_data):
    """ Check if video already exists in the data based on video_id. """
    return any(video['Video ID'] == video_id for video in existing_data)

def get_transcript(video_id):
    """ Fetch transcript for given video_id if subtitles are available. """
    try:
        if subtitles_available(video_id):
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join(part['text'] for part in transcript_list)
    except Exception as e:
        logging.error(f"Failed to retrieve transcript for video ID {video_id}: {str(e)}")
    return None

def subtitles_available(video_id):
    """ Check if subtitles are available for the video. """
    try:
        YouTubeTranscriptApi.list_transcripts(video_id)
        return True
    except Exception as e:
        logging.error(f"No subtitles available for video ID {video_id}: {str(e)}")
        return False

def parse_video_info():
    """ Main function to parse video information and save new data if not duplicate. """
    existing_data = load_existing_data("transcript.json")
    new_data_added = False

    try:
        with open('youtube_videos.json', "r") as file:
            data = json.load(file)
            for video in data.get('Videos', []):
                video_id = video.get('Video ID')
                if video_id and not video_already_exists(video_id, existing_data):
                    transcript = get_transcript(video_id)
                    if transcript:
                        video_data = {
                            "Video Name": video.get('Video Name'),
                            "Channel Creator Name": video.get('Channel Creator Name'),
                            "Date Added to YouTube": video.get('Date Added to YouTube'),
                            "Video ID": video_id,
                            "Link to the Video": video.get('Link to the Video'),
                            "Video Transcript": transcript
                        }
                        existing_data.append(video_data)
                        new_data_added = True
                else:
                    logging.info(f"Video ID {video_id} already exists or is missing.")
    except Exception as e:
        logging.error(f"Error processing video information: {str(e)}")

    if new_data_added:
        save_transcript(existing_data)

def save_transcript(data):
    """ Save the collected data to a JSON file, ensuring the file isn't empty. """
    with open("transcript.json", "w") as file:
        json.dump(data, file, indent=4)

if __name__ == "__main__":
    parse_video_info()
