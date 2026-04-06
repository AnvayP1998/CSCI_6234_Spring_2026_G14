import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import TaskRequestORM, TaskResultORM
from app.services.search_service import SearchService
from app.services.gemini_service import call_gemini

_search = SearchService()

SUPPORTED_TASKS = {"summarize", "qa", "classify"}


def _build_prompt(task_type: str, query: Optional[str], context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)

    if task_type == "summarize":
        return (
            "You are a document analyst. Based on the following document excerpts, "
            "write a concise and clear summary.\n\n"
            f"DOCUMENT EXCERPTS:\n{context}\n\n"
            "SUMMARY:"
        )

    if task_type == "qa":
        if not query:
            raise ValueError("task_type 'qa' requires a query.")
        return (
            "You are a helpful assistant. Answer the question below using ONLY "
            "the provided document excerpts. If the answer is not in the excerpts, "
            "say 'I could not find an answer in the provided document.'\n\n"
            f"DOCUMENT EXCERPTS:\n{context}\n\n"
            f"QUESTION: {query}\n\n"
            "ANSWER:"
        )

    if task_type == "classify":
        return (
            "You are a document classifier. Based on the following document excerpts, "
            "identify the document type and main topic in 1-2 sentences.\n\n"
            f"DOCUMENT EXCERPTS:\n{context}\n\n"
            "CLASSIFICATION:"
        )

    raise ValueError(f"Unsupported task_type: {task_type}")


class AnalysisService:

    def run_task(
        self,
        asset_id: str,
        task_type: str,
        query: Optional[str],
        db: Session,
    ) -> dict:
        if task_type not in SUPPORTED_TASKS:
            raise ValueError(f"task_type must be one of {SUPPORTED_TASKS}")

        # 1. Save TaskRequest
        request_id = str(uuid.uuid4())
        task_request = TaskRequestORM(
            request_id=request_id,
            asset_id=asset_id,
            task_type=task_type,
            query=query,
            created_at=datetime.utcnow(),
        )
        db.add(task_request)
        db.commit()

        # 2. Retrieve top relevant chunks from Qdrant
        search_query = query if (task_type == "qa" and query) else task_type
        hits = _search.search(query=search_query, top_k=6, asset_id=asset_id)

        if not hits:
            raise ValueError(
                f"No indexed content found for asset {asset_id}. "
                "Run /embed first."
            )

        context_chunks = [h.text for h in hits]

        # 3. Build prompt and call Gemini
        prompt = _build_prompt(task_type, query, context_chunks)
        answer = call_gemini(prompt)

        # 4. Save TaskResult
        result_id = str(uuid.uuid4())
        task_result = TaskResultORM(
            result_id=result_id,
            request_id=request_id,
            answer=answer,
            confidence=round(float(hits[0].score), 4) if hits else 0.0,
        )
        db.add(task_result)
        db.commit()

        return {
            "request_id": request_id,
            "result_id": result_id,
            "asset_id": asset_id,
            "task_type": task_type,
            "answer": answer,
            "confidence": task_result.confidence,
        }
