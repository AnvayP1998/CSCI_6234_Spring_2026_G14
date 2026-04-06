import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.models import DataAssetORM, ExtractedTextORM, ProcessingContextORM
from app.services.processing.document_processor import extract_text as extract_document_text
from app.services.processing.image_processor import extract_text_from_image
from app.services.processing.audio_processor import extract_text_from_audio, extract_text_from_video


class ProcessingService:

    def process_asset(self, asset_id: str, db: Session) -> dict:
        """
        Read asset from DB, extract text based on modality,
        persist ExtractedText + ProcessingContext, return summary.
        """
        asset: DataAssetORM = db.query(DataAssetORM).filter(
            DataAssetORM.asset_id == asset_id
        ).first()

        if asset is None:
            raise ValueError(f"Asset not found: {asset_id}")

        # --- create or update ProcessingContext to IN_PROGRESS ---
        ctx = db.query(ProcessingContextORM).filter(
            ProcessingContextORM.asset_id == asset_id
        ).first()

        if ctx is None:
            ctx = ProcessingContextORM(
                context_id=str(uuid.uuid4()),
                asset_id=asset_id,
                status="IN_PROGRESS",
                updated_at=datetime.utcnow(),
            )
            db.add(ctx)
        else:
            ctx.status = "IN_PROGRESS"
            ctx.updated_at = datetime.utcnow()

        db.commit()

        # --- dispatch extraction by modality ---
        try:
            modality = asset.asset_type
            file_path = asset.source_uri

            if modality == "document":
                extracted = extract_document_text(file_path)
            elif modality == "image":
                extracted = extract_text_from_image(file_path)
            elif modality == "audio":
                extracted = extract_text_from_audio(file_path)
            elif modality == "video":
                extracted = extract_text_from_video(file_path)
            else:
                extracted = f"[Unknown modality: {modality}]"

        except Exception as exc:
            ctx.status = "FAILED"
            ctx.updated_at = datetime.utcnow()
            db.commit()
            raise RuntimeError(f"Extraction failed: {exc}") from exc

        # --- persist ExtractedText (upsert: delete old if exists) ---
        existing = db.query(ExtractedTextORM).filter(
            ExtractedTextORM.asset_id == asset_id
        ).first()

        if existing:
            existing.content = extracted
            existing.language = "en"
        else:
            extracted_row = ExtractedTextORM(
                text_id=str(uuid.uuid4()),
                asset_id=asset_id,
                content=extracted,
                language="en",
            )
            db.add(extracted_row)

        # --- mark ProcessingContext PROCESSED ---
        ctx.status = "PROCESSED"
        ctx.updated_at = datetime.utcnow()
        db.commit()

        return {
            "asset_id": asset_id,
            "modality": modality,
            "status": "PROCESSED",
            "text_length": len(extracted),
        }
