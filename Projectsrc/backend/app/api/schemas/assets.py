from typing import Optional
from pydantic import BaseModel
from datetime import datetime


class AssetOut(BaseModel):
    asset_id: str
    filename: Optional[str]
    modality: str
    created_at: datetime
    processing_status: str


class AssetUploadResponse(AssetOut):
    pass


class AssetProcessResponse(BaseModel):
    asset_id: str
    modality: str
    status: str
    text_length: int


class AssetEmbedResponse(BaseModel):
    asset_id: str
    chunks_indexed: int
