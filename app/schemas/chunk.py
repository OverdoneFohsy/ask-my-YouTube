from typing import List, Optional
from pydantic import BaseModel

class Chunk(BaseModel):
    text: str
    start: float
    end: float

class ChunkResponse(BaseModel):
    video_id: str
    chunk: List[Chunk]