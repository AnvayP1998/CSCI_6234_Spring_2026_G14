from typing import Optional, List
from pydantic import BaseModel


class HistoryMessage(BaseModel):
    role: str     # "user" | "assistant"
    content: str


class AnalyzeRequest(BaseModel):
    asset_id: str
    task_type: str          # "summarize" | "qa" | "classify"
    query: Optional[str] = None  # required only for task_type="qa"
    history: List[HistoryMessage] = []  # last N conversation turns for context


class AnalyzeResponse(BaseModel):
    request_id: str
    result_id: str
    asset_id: str
    task_type: str
    answer: str
    confidence: float


class EvidenceResponse(BaseModel):
    evidence_id: str
    asset_id: str
    location: str   # e.g. "chunk 3"
    snippet: str    # first 300 chars of the chunk


class TaskResultResponse(BaseModel):
    request_id: str
    result_id: str
    asset_id: str
    task_type: str
    query: Optional[str]
    answer: str
    confidence: float
    evidence: List[EvidenceResponse]
