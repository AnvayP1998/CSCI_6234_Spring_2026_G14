from sqlalchemy.orm import Session

from app.domain.models import ExtractedTextORM
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embed_chunks
from app.services.qdrant_service import upsert_chunks


class IndexingService:

    def index_asset(self, asset_id: str, db: Session) -> dict:
        """
        Read extracted text from DB, chunk it, embed each chunk,
        and upsert vectors into Qdrant.
        """
        row: ExtractedTextORM = db.query(ExtractedTextORM).filter(
            ExtractedTextORM.asset_id == asset_id
        ).first()

        if row is None:
            raise ValueError(
                f"No extracted text found for asset {asset_id}. "
                "Run /process first."
            )

        chunks = chunk_text(row.content)
        if not chunks:
            raise ValueError("Extracted text produced no chunks.")

        embeddings = embed_chunks(chunks)
        num_upserted = upsert_chunks(asset_id, chunks, embeddings)

        return {
            "asset_id": asset_id,
            "chunks_indexed": num_upserted,
        }
