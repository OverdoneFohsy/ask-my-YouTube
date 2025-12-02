from fastapi import FastAPI
from app.api.transcript import router as transcript_router
from app.api.chunk import router as chunk_router

app = FastAPI(title="Ask My Youtuber Backend")

app.include_router(transcript_router, prefix="/api", tags=["Transcript"])
app.include_router(chunk_router, prefix="/api", tags=["Chunk"])

@app.get("/")
def root():
     return {"Message": "Backend is running"}  