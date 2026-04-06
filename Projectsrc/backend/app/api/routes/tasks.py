from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.api.schemas.tasks import AnalyzeRequest, AnalyzeResponse
from app.services.analysis_service import AnalysisService

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
