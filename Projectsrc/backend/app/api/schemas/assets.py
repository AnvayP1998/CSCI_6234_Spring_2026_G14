from pydantic import BaseModel
from datetime import datetime

class AssetUploadResponse(BaseModel):
    asset_id: str
    modality: str
    source_uri: str
    created_at: datetime