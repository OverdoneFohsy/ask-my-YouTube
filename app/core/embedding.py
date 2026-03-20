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
import time
from typing import List
from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Embeds text using Google's gemini-embedding-001 model.
    Includes batching to prevent Render Out-of-Memory crashes.
    """
    all_embeddings = []
    batch_size = 100
    
    try:
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=batch,
                config={
                    "output_dimensionality": 384  # Matches your Pinecone index
                }
            )
            
            # Extract vectors and add to our main list
            batch_vectors = [item.values for item in response.embeddings]
            all_embeddings.extend(batch_vectors)
            
            # Small breather for Render's CPU/RAM
            time.sleep(0.2) 
            
        return all_embeddings

    except Exception as e:
        print(f"Error during Google Embedding: {e}")
        raise e