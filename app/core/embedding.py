# from sentence_transformers import SentenceTransformer
# from typing import List

# embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# def get_embedding_model() -> SentenceTransformer:
#     return embedding_model

# def embed_texts(texts: List[str]) -> List[List[float]]:
#     model = get_embedding_model()

#     embeddings = model.encode(texts, convert_to_tensor=False)

#     return embeddings.tolist()

import os
from typing import List
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def embed_texts(texts: List[str]) -> List[List[float]]:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config={"output_dimensionality": 384}
    )
    
    embeddings = [item.values for item in response.embeddings]
    return embeddings