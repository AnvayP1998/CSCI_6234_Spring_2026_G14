from fastapi import APIRouter, HTTPException
from app.api.schemas.query import QueryRequest, QueryResponse, SearchHitResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["query"])

search_service = SearchService()


@router.get("/query/ping")
def query_ping():
    return {"status": "query route ok"}


@router.post("/query", response_model=QueryResponse)
def query_assets(request: QueryRequest):
    try:
        hits = search_service.search(
            query=request.query,
            top_k=request.top_k,
            asset_id=request.asset_id,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return QueryResponse(
        query=request.query,
        hits=[
            SearchHitResponse(
                asset_id=h.asset_id,
                chunk_index=h.chunk_index,
                text=h.text,
                score=h.score,
            )
            for h in hits
        ],
    )