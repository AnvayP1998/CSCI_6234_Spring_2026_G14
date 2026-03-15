import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.domain.models import DataAssetORM
from app.api.schemas.assets import AssetUploadResponse
from app.services.storage_service import StorageService
from app.services.modality_service import detect_modality

router = APIRouter(tags=["assets"])

storage = StorageService()

@router.post("/assets/upload", response_model=AssetUploadResponse)
async def upload_asset(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    modality = detect_modality(file.filename)

    # 1) save file
    stored_path = await storage.save_file(file)

    # 2) write to DB
    asset_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    db: Session = SessionLocal()
    try:
        asset = DataAssetORM(
            asset_id=asset_id,
            source_uri=stored_path,
            modality=modality,
            created_at=created_at,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    finally:
        db.close()

    # 3) return response
    return AssetUploadResponse(
        asset_id=asset.asset_id,
        modality=asset.modality,
        source_uri=asset.source_uri,
        created_at=asset.created_at,
    )