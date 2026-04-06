from typing import List, Optional
from app.services.embedding_service import embed_chunks
from app.services.qdrant_service import get_client, ensure_collection
from app.core.config import settings


class SearchHit:
    def __init__(self, asset_id: str, chunk_index: int, text: str, score: float):
        self.asset_id = asset_id
        self.chunk_index = chunk_index
        self.text = text
        self.score = score


class SearchService:

    def search(
        self,
        query: str,
        top_k: int = 5,
        asset_id: Optional[str] = None,
    ) -> List[SearchHit]:
        """
        Embed the query, search Qdrant for top_k similar chunks.
        Optionally filter by asset_id.
        """
        # Embed the query (reuse same model as indexing)
        query_vector = embed_chunks([query])[0]

        client = get_client()
        ensure_collection()

        # Build optional filter
        query_filter = None
        if asset_id:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            query_filter = Filter(
                must=[FieldCondition(key="asset_id", match=MatchValue(value=asset_id))]
            )

        results = client.search(
            collection_name=settings.QDRANT_COLLECTION,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        hits = []
        for r in results:
            payload = r.payload or {}
            hits.append(SearchHit(
                asset_id=payload.get("asset_id", ""),
                chunk_index=payload.get("chunk_index", -1),
                text=payload.get("text", ""),
                score=r.score,
            ))

        return hits
