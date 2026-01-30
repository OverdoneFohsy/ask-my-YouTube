from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import transcript, chunk, ingestion, embedding, query, session, auth
from app.core.database import engine, Base
from app.core.auth import security

load_dotenv()



Base.metadata.create_all(bind=engine)

app = FastAPI(
     title="Ask My Youtuber Backend",
     swagger_ui_parameters={"persistAuthorization": True})

app.include_router(transcript.router, prefix="/api", tags=["Transcript"])
app.include_router(chunk.router, prefix="/api", tags=["Chunk"])
app.include_router(embedding.router, prefix="/api", tags=["Embedding"])
app.include_router(ingestion.router, prefix="/api", tags=["Ingestion"])
app.include_router(query.router, prefix="/api", tags=["query"])
app.include_router(session.router, prefix="/api", tags=["session"])
app.include_router(auth.router, prefix="/api", tags=["auth"])

@app.get("/")
def root():
     return {"Message": "Backend is running"}  