import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.domain.models import TaskRequestORM, TaskResultORM, EvidenceRefORM
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
            "You are a helpful assistant. Answer the question below using the "
            "provided document excerpts. Be thorough and complete — if the question "
            "asks about multiple items (e.g. 'all phases', 'all types', 'all rules'), "
            "list every one you can find in the excerpts. If information is partially "
            "present, include what you have and note what is missing. Only say "
            "'I could not find an answer' if the topic is entirely absent.\n\n"
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

        # 2. Retrieve relevant chunks from Qdrant
        # For broad "all X" questions, run extra targeted searches and merge
        search_query = query if (task_type == "qa" and query) else task_type
        hits = _search.search(query=search_query, top_k=30, asset_id=asset_id)

        broad_keywords = ["all", "every", "each", "list", "define", "phases",
                          "types", "rules", "steps", "summarize"]
        is_broad = task_type in ("summarize", "classify") or any(
            kw in (query or "").lower() for kw in broad_keywords
        )
        if is_broad and query:
            # Additional targeted search to catch sections missed by the main query
            extra = _search.search(
                query=f"section heading {query}", top_k=10, asset_id=asset_id
            )
            seen_ids = {h.chunk_index for h in hits}
            for h in extra:
                if h.chunk_index not in seen_ids:
                    hits.append(h)
                    seen_ids.add(h.chunk_index)

        if not hits:
            raise ValueError(
                f"No indexed content found for asset {asset_id}. "
                "Run /embed first."
            )

        # Sort by chunk_index so context reads in document order
        hits.sort(key=lambda h: h.chunk_index)
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

        # 5. Save EvidenceRefs — one per chunk used as context
        for hit in hits:
            evidence = EvidenceRefORM(
                evidence_id=str(uuid.uuid4()),
                result_id=result_id,
                asset_id=hit.asset_id,
                location=f"chunk {hit.chunk_index}",
                snippet=hit.text[:300],
            )
            db.add(evidence)
        db.commit()

        return {
            "request_id": request_id,
            "result_id": result_id,
            "asset_id": asset_id,
            "task_type": task_type,
            "answer": answer,
            "confidence": task_result.confidence,
        }
