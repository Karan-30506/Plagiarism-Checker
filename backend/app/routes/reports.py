"""
reports.py  —  Person 2 (Part 1): Indexing, Candidate Search & Top-K Ranking
=============================================================================

Endpoints implemented here:
  POST /api/reports/check          — Run full plagiarism check on a source document.
  GET  /api/reports/summary        — Retrieve stored report summaries for the current user.
  GET  /api/reports/{report_id}    — Retrieve a single detailed report.

Pipeline (P2 scope):
  1. Load query document fingerprints from the DB.
  2. Build corpus index (all other documents' fingerprints) from the DB.
  3. Invoke C++ 'query' mode:
       a. Compressed Radix Trie  — O(L) hash lookup per query fingerprint.
       b. Jaccard similarity     — intersection / union over fingerprint sets.
       c. Max-Binomial Heap      — extract Top-K ranked candidates in O(K log N).
  4. Persist PlagiarismReport rows to PostgreSQL.
  5. Return structured JSON for the frontend top_k_table component.

Note: /api/reports/diff and /api/reports/collusion-graph are Person 3's scope
      and will be added in reports.py Part 2.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from app.database import get_db
from app.models import Document, PlagiarismReport
from app.auth import get_current_user
from app.engine_bridge import query_trie_top_k

router = APIRouter(prefix="/api/reports", tags=["Plagiarism Reports"])


# ---------------------------------------------------------------------------
# Helper: build corpus index from DB (excludes the source document itself)
# ---------------------------------------------------------------------------
def _build_corpus_index(
    db: Session,
    exclude_doc_id: uuid.UUID
) -> dict[str, list[int]]:
    """
    Fetches all documents except the query document and converts their
    JSONB fingerprint arrays into the format expected by query_trie_top_k:
      { doc_id_str: [hash_int, ...] }
    """
    docs = db.query(Document).filter(Document.id != exclude_doc_id).all()

    corpus: dict[str, list[int]] = {}
    for doc in docs:
        if not doc.fingerprints:
            continue
        # fingerprints JSONB is stored as list of {"hash": int, "position": int}
        hashes = [fp["hash"] for fp in doc.fingerprints if "hash" in fp]
        if hashes:
            corpus[str(doc.id)] = hashes

    return corpus


# ---------------------------------------------------------------------------
# POST /api/reports/check
# ---------------------------------------------------------------------------
@router.post("/check")
def check_document(
    payload: dict,          # { "source_doc_id": "<uuid>", "top_k": 10 }
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Full plagiarism-check pipeline (P2 scope):
    Compressed Trie lookup → Jaccard similarity → Max-Binomial Heap Top-K.

    Request body:
      {
        "source_doc_id": "uuid-string",
        "top_k": 10           (optional, default 10)
      }

    Response:
      {
        "source_doc_id": "...",
        "source_filename": "...",
        "top_k_matches": [
          {
            "rank": 1,
            "doc_id": "...",
            "filename": "...",
            "similarity_score": 0.87,
            "report_id": "..."
          },
          ...
        ]
      }
    """
    source_doc_id_str = payload.get("source_doc_id")
    top_k = int(payload.get("top_k", 10))

    if not source_doc_id_str:
        raise HTTPException(status_code=400, detail="source_doc_id is required.")

    # --- 1. Fetch source document ---
    try:
        source_uuid = uuid.UUID(source_doc_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid source_doc_id format.")

    source_doc = db.query(Document).filter(Document.id == source_uuid).first()
    if not source_doc:
        raise HTTPException(status_code=404, detail="Source document not found.")

    query_fingerprints: list[dict] = source_doc.fingerprints or []
    if not query_fingerprints:
        raise HTTPException(
            status_code=422,
            detail="Source document has no fingerprints. Re-upload the document."
        )

    # --- 2. Build corpus index from all other documents ---
    corpus_index = _build_corpus_index(db, exclude_doc_id=source_uuid)
    if not corpus_index:
        return {
            "source_doc_id": source_doc_id_str,
            "source_filename": source_doc.filename,
            "top_k_matches": [],
            "message": "No other documents in corpus to compare against."
        }

    # --- 3. C++: Compressed Trie + Jaccard + Max-Binomial Heap ---
    try:
        ranked_candidates = query_trie_top_k(
            query_fingerprints=query_fingerprints,
            corpus_index=corpus_index,
            top_k=top_k
        )
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"C++ engine not found. Build the project first. ({e})"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"C++ query engine error: {str(e)}"
        )

    # --- 4. Persist PlagiarismReport rows & enrich with filenames ---
    top_k_response = []

    for rank, candidate in enumerate(ranked_candidates, start=1):
        matched_doc_id_str = candidate["doc_id"]
        similarity_score   = float(candidate["similarity_score"])

        try:
            matched_uuid = uuid.UUID(matched_doc_id_str)
        except ValueError:
            continue

        matched_doc = db.query(Document).filter(Document.id == matched_uuid).first()
        if not matched_doc:
            continue

        # Upsert: check if a report already exists for this pair
        existing_report = db.query(PlagiarismReport).filter(
            PlagiarismReport.source_doc_id == source_uuid,
            PlagiarismReport.matched_doc_id == matched_uuid
        ).first()

        if existing_report:
            # Update score if re-checked
            existing_report.similarity_score = similarity_score
            db.commit()
            report_id = str(existing_report.id)
        else:
            new_report = PlagiarismReport(
                source_doc_id=source_uuid,
                matched_doc_id=matched_uuid,
                similarity_score=similarity_score,
                matched_segments=[]    # Filled by P3 (diff engine)
            )
            db.add(new_report)
            db.commit()
            db.refresh(new_report)
            report_id = str(new_report.id)

        top_k_response.append({
            "rank": rank,
            "doc_id": matched_doc_id_str,
            "filename": matched_doc.filename,
            "similarity_score": round(similarity_score, 4),
            "report_id": report_id
        })

    return {
        "source_doc_id": source_doc_id_str,
        "source_filename": source_doc.filename,
        "top_k_matches": top_k_response
    }


# ---------------------------------------------------------------------------
# GET /api/reports/summary
# ---------------------------------------------------------------------------
@router.get("/summary")
def get_report_summary(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns all plagiarism report summaries for documents owned by the current user.

    Response: list of report objects with source filename, match filename, and score.
    """
    user_id_str = current_user["id"]
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID in token.")

    # Get all documents belonging to this user
    user_docs = db.query(Document).filter(Document.user_id == user_uuid).all()
    user_doc_ids = {doc.id for doc in user_docs}

    if not user_doc_ids:
        return []

    # Get all reports where the source document belongs to this user
    reports = db.query(PlagiarismReport).filter(
        PlagiarismReport.source_doc_id.in_(user_doc_ids)
    ).order_by(PlagiarismReport.created_at.desc()).all()

    # Build a quick lookup for filenames
    doc_map = {doc.id: doc.filename for doc in user_docs}

    result = []
    for report in reports:
        matched_doc = db.query(Document).filter(
            Document.id == report.matched_doc_id
        ).first()
        matched_filename = matched_doc.filename if matched_doc else "Unknown"

        result.append({
            "report_id": str(report.id),
            "source_doc_id": str(report.source_doc_id),
            "source_filename": doc_map.get(report.source_doc_id, "Unknown"),
            "matched_doc_id": str(report.matched_doc_id),
            "matched_filename": matched_filename,
            "similarity_score": round(report.similarity_score, 4),
            "created_at": report.created_at.isoformat() if report.created_at else None
        })

    return result


# ---------------------------------------------------------------------------
# GET /api/reports/{report_id}
# ---------------------------------------------------------------------------
@router.get("/{report_id}")
def get_report_detail(
    report_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the full detail of a single plagiarism report, including any
    matched_segments (line offsets) filled in by Person 3's diff engine.

    Response:
      {
        "report_id": "...",
        "source_doc_id": "...",
        "source_filename": "...",
        "matched_doc_id": "...",
        "matched_filename": "...",
        "similarity_score": 0.87,
        "matched_segments": [...],
        "created_at": "..."
      }
    """
    try:
        report_uuid = uuid.UUID(report_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid report_id format.")

    report = db.query(PlagiarismReport).filter(
        PlagiarismReport.id == report_uuid
    ).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")

    # Verify ownership: source document must belong to current user
    user_id_str = current_user["id"]
    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID in token.")

    source_doc = db.query(Document).filter(
        Document.id == report.source_doc_id
    ).first()

    if not source_doc or source_doc.user_id != user_uuid:
        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this report."
        )

    matched_doc = db.query(Document).filter(
        Document.id == report.matched_doc_id
    ).first()

    return {
        "report_id": str(report.id),
        "source_doc_id": str(report.source_doc_id),
        "source_filename": source_doc.filename,
        "matched_doc_id": str(report.matched_doc_id),
        "matched_filename": matched_doc.filename if matched_doc else "Unknown",
        "similarity_score": round(report.similarity_score, 4),
        "matched_segments": report.matched_segments or [],
        "created_at": report.created_at.isoformat() if report.created_at else None
    }

