from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.api.schemas.tasks import AnalyzeRequest, AnalyzeResponse, TaskResultResponse, EvidenceResponse
from app.services.analysis_service import AnalysisService
from app.domain.models import TaskRequestORM, TaskResultORM, EvidenceRefORM

router = APIRouter(tags=["tasks"])

analysis = AnalysisService()


@router.post("/tasks/analyze", response_model=AnalyzeResponse)
def analyze_asset(request: AnalyzeRequest):
    db: Session = SessionLocal()
    try:
        result = analysis.run_task(
            asset_id=request.asset_id,
            task_type=request.task_type,
            query=request.query,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

    return AnalyzeResponse(**result)


@router.get("/tasks/{request_id}/result", response_model=TaskResultResponse)
def get_task_result(request_id: str):
    db: Session = SessionLocal()
    try:
        task_req = db.query(TaskRequestORM).filter(
            TaskRequestORM.request_id == request_id
        ).first()
        if task_req is None:
            raise HTTPException(status_code=404, detail="Task request not found")

        task_res = db.query(TaskResultORM).filter(
            TaskResultORM.request_id == request_id
        ).first()
        if task_res is None:
            raise HTTPException(status_code=404, detail="Task result not found")

        evidence_rows = db.query(EvidenceRefORM).filter(
            EvidenceRefORM.result_id == task_res.result_id
        ).all()

        evidence = [
            EvidenceResponse(
                evidence_id=e.evidence_id,
                asset_id=e.asset_id,
                location=e.location,
                snippet=e.snippet,
            )
            for e in evidence_rows
        ]
    finally:
        db.close()

    return TaskResultResponse(
        request_id=task_req.request_id,
        result_id=task_res.result_id,
        asset_id=task_req.asset_id,
        task_type=task_req.task_type,
        query=task_req.query,
        answer=task_res.answer,
        confidence=task_res.confidence,
        evidence=evidence,
    )
