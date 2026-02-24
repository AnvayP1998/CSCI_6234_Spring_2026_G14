from fastapi import APIRouter

router = APIRouter()

@router.get("/assets/ping")
def assets_ping():
    return {"status": "assets route ok"}