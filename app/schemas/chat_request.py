from typing import Optional
from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str
    source_id: Optional[str] = None
    top_k: Optional[int] = None