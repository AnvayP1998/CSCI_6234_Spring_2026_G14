import mimetypes
import os
import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.domain.models import DataAssetORM, ProcessingContextORM, ExtractedTextORM, TaskRequestORM, TaskResultORM, EvidenceRefORM
from app.api.schemas.assets import AssetOut, AssetUploadResponse, AssetProcessResponse, AssetEmbedResponse, AssetTextResponse
from app.services.storage_service import StorageService
from app.services.modality_service import detect_modality
from app.services.processing_service import ProcessingService
from app.services.indexing_service import IndexingService
from app.services.qdrant_service import count_chunks, delete_chunks

router = APIRouter(tags=["assets"])

storage = StorageService()
processing = ProcessingService()
indexing = IndexingService()


def _asset_with_status(asset: DataAssetORM, db: Session) -> AssetOut:
    ctx = db.query(ProcessingContextORM).filter(
        ProcessingContextORM.asset_id == asset.asset_id
    ).first()
    return AssetOut(
        asset_id=asset.asset_id,
        filename=asset.filename,
        modality=asset.asset_type,
        created_at=asset.created_at,
        processing_status=ctx.status if ctx else "UPLOADED",
        chunks_indexed=count_chunks(asset.asset_id),
    )


@router.get("/assets", response_model=List[AssetOut])
def list_assets():
    db: Session = SessionLocal()
    try:
        assets = db.query(DataAssetORM).order_by(DataAssetORM.created_at.desc()).all()
        return [_asset_with_status(a, db) for a in assets]
    finally:
        db.close()


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str):
    db: Session = SessionLocal()
    try:
        asset = db.query(DataAssetORM).filter(DataAssetORM.asset_id == asset_id).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        return _asset_with_status(asset, db)
    finally:
        db.close()


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
            filename=file.filename,
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
        filename=asset.filename,
        modality=asset.asset_type,
        created_at=asset.created_at,
        processing_status="UPLOADED",
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


@router.get("/assets/{asset_id}/file")
def get_asset_file(asset_id: str):
    db: Session = SessionLocal()
    try:
        asset = db.query(DataAssetORM).filter(DataAssetORM.asset_id == asset_id).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")
        if not asset.source_uri or not os.path.exists(asset.source_uri):
            raise HTTPException(status_code=404, detail="File not found on disk")
        mime_type, _ = mimetypes.guess_type(asset.source_uri)
        return FileResponse(
            path=asset.source_uri,
            media_type=mime_type or "application/octet-stream",
            filename=asset.filename or "file",
        )
    finally:
        db.close()


@router.get("/assets/{asset_id}/text", response_model=AssetTextResponse)
def get_asset_text(asset_id: str):
    db: Session = SessionLocal()
    try:
        extracted = db.query(ExtractedTextORM).filter(
            ExtractedTextORM.asset_id == asset_id
        ).first()
        if extracted is None:
            raise HTTPException(status_code=404, detail="No extracted text found. Run Extract Text first.")
        return AssetTextResponse(
            asset_id=asset_id,
            text_length=len(extracted.content),
            content=extracted.content,
        )
    finally:
        db.close()


@router.delete("/assets/{asset_id}", status_code=204)
def delete_asset(asset_id: str):
    db: Session = SessionLocal()
    try:
        asset = db.query(DataAssetORM).filter(DataAssetORM.asset_id == asset_id).first()
        if asset is None:
            raise HTTPException(status_code=404, detail="Asset not found")

        # Delete file from disk
        if asset.source_uri and os.path.exists(asset.source_uri):
            os.remove(asset.source_uri)

        # Delete vectors from Qdrant
        delete_chunks(asset_id)

        # Delete related DB rows manually (no cascade on task_requests/evidence_refs)
        requests = db.query(TaskRequestORM).filter(TaskRequestORM.asset_id == asset_id).all()
        for req in requests:
            db.query(EvidenceRefORM).filter(EvidenceRefORM.result_id.in_(
                db.query(TaskResultORM.result_id).filter(TaskResultORM.request_id == req.request_id)
            )).delete(synchronize_session=False)
            db.query(TaskResultORM).filter(TaskResultORM.request_id == req.request_id).delete(synchronize_session=False)
        db.query(TaskRequestORM).filter(TaskRequestORM.asset_id == asset_id).delete(synchronize_session=False)
        db.query(EvidenceRefORM).filter(EvidenceRefORM.asset_id == asset_id).delete(synchronize_session=False)
        db.query(ProcessingContextORM).filter(ProcessingContextORM.asset_id == asset_id).delete(synchronize_session=False)
        db.query(ExtractedTextORM).filter(ExtractedTextORM.asset_id == asset_id).delete(synchronize_session=False)
        db.delete(asset)
        db.commit()
    finally:
        db.close()


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
