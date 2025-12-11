from typing import List, Optional
from pydantic import BaseModel

class Chunk(BaseModel):
    video_id: str
    text: str
    start: float
    end: float
    vector: Optional[List[float]] = None

class ChunkResponse(BaseModel):
    video_id: str
    chunk: List[Chunk]