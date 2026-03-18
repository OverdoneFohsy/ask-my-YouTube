from fastapi import FastAPI
from dotenv import load_dotenv
from app.api import transcript, chunk, ingestion, embedding, query, session, auth
from app.core.database import engine, Base
from app.core.auth import security
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

Base.metadata.create_all(bind=engine)

app = FastAPI(
     title="Learner Archive Backend",
     swagger_ui_parameters={"persistAuthorization": True})

origins = [
    "http://localhost:3000", # For local development
    "https://learner-archive-frontend.vercel.app", # Your actual Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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