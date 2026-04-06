import uuid
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.domain.models import DataAssetORM
from app.api.schemas.assets import AssetUploadResponse, AssetProcessResponse, AssetEmbedResponse
from app.services.storage_service import StorageService
from app.services.modality_service import detect_modality
from app.services.processing_service import ProcessingService
from app.services.indexing_service import IndexingService

router = APIRouter(tags=["assets"])

storage = StorageService()
processing = ProcessingService()
indexing = IndexingService()


@router.post("/assets/upload", response_model=AssetUploadResponse)
async def upload_asset(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing filename")

    asset_type = detect_modality(file.filename)

    stored_path = await storage.save_file(file)

    asset_id = str(uuid.uuid4())
    created_at = datetime.utcnow()

    db: Session = SessionLocal()
    try:
        asset = DataAssetORM(
            asset_id=asset_id,
            source_uri=stored_path,
            asset_type=asset_type,
            created_at=created_at,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
    finally:
        db.close()

    return AssetUploadResponse(
        asset_id=asset.asset_id,
        modality=asset.asset_type,
        source_uri=asset.source_uri,
        created_at=asset.created_at,
    )


@router.post("/assets/{asset_id}/process", response_model=AssetProcessResponse)
def process_asset(asset_id: str):
    db: Session = SessionLocal()
    try:
        result = processing.process_asset(asset_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return AssetProcessResponse(**result)


@router.post("/assets/{asset_id}/embed", response_model=AssetEmbedResponse)
def embed_asset(asset_id: str):
    db: Session = SessionLocal()
    try:
        result = indexing.index_asset(asset_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return AssetEmbedResponse(**result)