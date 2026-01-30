import requests
from fastapi import APIRouter, HTTPException
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    VideoUnavailable,
    # TooManyRequests
)
import re

from app.schemas.transcript import TranscriptResponse, Snippet

from pytube import YouTube

def extract_video_id(value: str) -> str:
    if re.fullmatch(r"[a-zA-Z0-9_-]{11}", value):
        return value
    
    patterns = [
        r"v=([a-zA-Z0-9_-]{11})",
        r"youtu\.be/([a-zA-Z0-9_-]{11})",
        r"youtube\.com/embed/([a-zA-Z0-9_-]{11})",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    raise ValueError("Invalid YouTube URL or video ID")

def get_video_title(video_id: str):
    try:
        url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return response.json().get("title", f"Video {video_id}")
    except Exception as e:
        raise ValueError(f"YouTube metadata fetch failed for {video_id}: {str(e)}")
    return f"Failed to fetch Video title {video_id} due to {response.status_code}"
class TranscriptService:

    def __init__(self):
        self.transcript_api = YouTubeTranscriptApi()
        
    def get_transcript(self, video_id: str):
        try:
            video_id = extract_video_id(video_id)
            title = get_video_title(video_id=video_id)
            transcript = self.transcript_api.fetch(video_id=video_id)
            
            # return transcript
            response = TranscriptResponse(
                    video_id = transcript.video_id,
                    title = title,
                    language = transcript.language,
                    language_code = transcript.language_code,
                    is_generated = transcript.is_generated,
                    snippets = [Snippet(text=snippet.text, start=snippet.start, duration=snippet.duration) for snippet in transcript.snippets]
            )
            
            return response

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        except VideoUnavailable:
            raise HTTPException(
                status_code=404,
                detail="The video is unavailable (private, removed, or region-locked)."
            )
        
        except TranscriptsDisabled:
            raise HTTPException(
                status_code=400,
                detail="Transcripts are disabled for this video."
            )
        
        except NoTranscriptFound:
            raise HTTPException(
                status_code=404,
                detail="No transcript found for this video."
            )
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )
        
def get_transcript_service():
    return TranscriptService()