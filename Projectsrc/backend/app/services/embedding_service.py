from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings

# Model is loaded once at module level (singleton — avoids reloading per request)
_model: SentenceTransformer | None = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _model


def embed_chunks(chunks: List[str]) -> List[List[float]]:
    """Return a list of embedding vectors, one per chunk."""
    model = get_model()
    embeddings = model.encode(chunks, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]
