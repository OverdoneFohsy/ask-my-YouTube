from typing import List, Optional
from pydantic import BaseModel

class Snippet(BaseModel):
    text: str
    start: float
    duration: float

class TranscriptResponse(BaseModel):
    video_id: str
    language: str
    language_code: str
    is_generated: bool
    snippets: List[Snippet]


