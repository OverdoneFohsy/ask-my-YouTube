from fastapi import FastAPI
from app.api import transcript, chunk, ingestion

app = FastAPI(title="Ask My Youtuber Backend")

app.include_router(transcript.router, prefix="/api", tags=["Transcript"])
app.include_router(chunk.router, prefix="/api", tags=["Chunk"])
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])

@app.get("/")
def root():
     return {"Message": "Backend is running"}  