from sentence_transformers import SentenceTransformer
from typing import List

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_embedding_model() -> SentenceTransformer:
    return embedding_model

def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()

    embeddings = model.encode(texts, convert_to_tensor=False)

    return embeddings.tolist()