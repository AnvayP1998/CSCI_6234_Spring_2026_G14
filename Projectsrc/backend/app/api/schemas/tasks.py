from typing import Optional
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    asset_id: str
    task_type: str          # "summarize" | "qa" | "classify"
    query: Optional[str] = None  # required only for task_type="qa"


class AnalyzeResponse(BaseModel):
    request_id: str
    result_id: str
    asset_id: str
    task_type: str
    answer: str
    confidence: float
