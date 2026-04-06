from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class DataAssetORM(Base):
    __tablename__ = "data_assets"

    asset_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_type: Mapped[str] = mapped_column(String(32), nullable=False)  # document|image|audio|video
    source_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    extracted_text: Mapped[Optional["ExtractedTextORM"]] = relationship(
        back_populates="asset", uselist=False, cascade="all, delete-orphan"
    )


class ExtractedTextORM(Base):
    __tablename__ = "extracted_texts"

    text_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.asset_id"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(16), default="en", nullable=False)

    asset: Mapped["DataAssetORM"] = relationship(back_populates="extracted_text")


class TaskRequestORM(Base):
    __tablename__ = "task_requests"

    request_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.asset_id"), nullable=True, index=True)
    task_type: Mapped[str] = mapped_column(String(32), nullable=False)  # summarize|qa|classify|search
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class TaskResultORM(Base):
    __tablename__ = "task_results"

    result_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    request_id: Mapped[str] = mapped_column(ForeignKey("task_requests.request_id"), nullable=False, index=True)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)


class EvidenceRefORM(Base):
    __tablename__ = "evidence_refs"

    evidence_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    result_id: Mapped[str] = mapped_column(ForeignKey("task_results.result_id"), nullable=False, index=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.asset_id"), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(128), nullable=False)  # "PDF p.12", "Audio 14:32"
    snippet: Mapped[str] = mapped_column(Text, nullable=False)

class ProcessingContextORM(Base):
    __tablename__ = "processing_contexts"

    context_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("data_assets.asset_id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="UPLOADED", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)