from pydantic import BaseModel
from datetime import datetime


class AssetUploadResponse(BaseModel):
    asset_id: str
    modality: str
    source_uri: str
    created_at: datetime


class AssetProcessResponse(BaseModel):
    asset_id: str
    modality: str
    status: str
    text_length: int


class AssetEmbedResponse(BaseModel):
    asset_id: str
    chunks_indexed: int