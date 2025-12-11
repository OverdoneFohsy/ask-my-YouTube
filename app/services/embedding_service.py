
from typing import List
from app.core.embedding import embed_texts

class EmbeddingService:

    def embed_texts(self, texts:List[str]) -> List[List[float]]:
        try:
            return embed_texts(texts=texts)
        except Exception as e:
            raise RuntimeError(f"Failed to embed texts due to {e}")

            
        
def get_embedding_service():
    return EmbeddingService()