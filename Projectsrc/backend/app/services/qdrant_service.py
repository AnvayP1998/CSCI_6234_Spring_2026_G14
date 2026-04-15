from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.core.config import settings

# Client is a singleton
_client: QdrantClient | None = None
VECTOR_SIZE = 384  # all-MiniLM-L6-v2 output dimension


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL)
    return _client


def ensure_collection() -> None:
    """Create the Qdrant collection if it doesn't exist."""
    client = get_client()
    existing = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in existing:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def count_chunks(asset_id: str) -> int:
    """Return the number of vectors indexed in Qdrant for this asset."""
    try:
        client = get_client()
        ensure_collection()
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        result = client.count(
            collection_name=settings.QDRANT_COLLECTION,
            count_filter=Filter(
                must=[FieldCondition(key="asset_id", match=MatchValue(value=asset_id))]
            ),
            exact=True,
        )
        return result.count
    except Exception:
        return 0


def delete_chunks(asset_id: str) -> None:
    """Delete all vectors for a given asset from Qdrant."""
    try:
        client = get_client()
        ensure_collection()
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        client.delete(
            collection_name=settings.QDRANT_COLLECTION,
            points_selector=Filter(
                must=[FieldCondition(key="asset_id", match=MatchValue(value=asset_id))]
            ),
        )
    except Exception:
        pass


def upsert_chunks(asset_id: str, chunks: List[str], embeddings: List[List[float]]) -> int:
    """
    Upsert chunk vectors into Qdrant.
    Each point carries asset_id, chunk_index, and a text snippet as payload.
    Returns number of points upserted.
    """
    client = get_client()
    ensure_collection()

    points = [
        PointStruct(
            id=abs(hash(f"{asset_id}_{i}")) % (2**63),
            vector=embeddings[i],
            payload={
                "asset_id": asset_id,
                "chunk_index": i,
                "text": chunks[i][:500],  # store first 500 chars as snippet
            },
        )
        for i in range(len(chunks))
    ]

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return len(points)
