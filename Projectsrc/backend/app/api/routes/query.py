from fastapi import APIRouter

router = APIRouter()

@router.get("/query/ping")
def query_ping():
    return {"status": "query route ok"}