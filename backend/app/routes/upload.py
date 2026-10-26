from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import uuid

from app.database import get_db
from app.models import Document
from app.auth import get_current_user
from app.utils import process_uploaded_payload
from app.engine_bridge import compress_text_huffman, decompress_text_huffman, get_winnow_fingerprints
from app.supabase_client import supabase_admin

router = APIRouter(prefix="/api/documents", tags=["Document Ingestion"])

class RenameDocumentRequest(BaseModel):
    new_filename: str

@router.post("/upload")
def upload_documents(
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    user_id_str = current_user["id"]
    try:
        user_id_uuid = uuid.UUID(str(user_id_str))
    except ValueError:
        user_id_uuid = user_id_str

    ingested_records = []

    for file in files:
        file_bytes = file.file.read()
        extracted_docs = process_uploaded_payload(file.filename, file_bytes)

        for doc_item in extracted_docs:
            filename = doc_item["filename"]
            raw_text = doc_item["raw_text"]
            norm_text = doc_item["normalized_text"]

            # --- STREAM A: C++ Huffman Compression ---
            comp_bytes, orig_size, comp_size = compress_text_huffman(raw_text)

            # Upload .bin payload to Supabase Storage Bucket ('compressed_docs')
            doc_uuid = uuid.uuid4()
            storage_path = f"{user_id_str}/{doc_uuid.hex}_{filename}.bin"
            try:
                supabase_admin.storage.from_("compressed_docs").upload(
                    path=storage_path,
                    file=comp_bytes,
                    file_options={"content-type": "application/octet-stream"}
                )
            except Exception as e:
                print(f"⚠️ Supabase Storage Upload Warning: {str(e)}")

            # --- STREAM B: C++ Winnowing Fingerprinting ---
            fps = get_winnow_fingerprints(norm_text if norm_text else raw_text)

            # --- DATABASE PERSISTENCE ---
            db_doc = Document(
                id=doc_uuid,
                user_id=user_id_uuid,
                filename=filename,
                storage_path=storage_path,
                original_size_bytes=orig_size,
                compressed_size_bytes=comp_size,
                fingerprints=fps
            )
            db.add(db_doc)

            ingested_records.append({
                "document_id": str(db_doc.id),
                "filename": filename,
                "original_size": orig_size,
                "compressed_size": comp_size,
                "fingerprint_count": len(fps),
                "storage_path": storage_path
            })

    db.commit()

    return {
        "status": "success",
        "message": f"Successfully ingested {len(ingested_records)} document(s).",
        "documents": ingested_records
    }


@router.get("/my-documents")
def get_user_documents(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user_id_str = current_user["id"]
    try:
        user_id_uuid = uuid.UUID(str(user_id_str))
        docs = db.query(Document).filter(Document.user_id == user_id_uuid).order_by(Document.created_at.desc()).all()
    except ValueError:
        docs = db.query(Document).filter(Document.user_id == user_id_str).order_by(Document.created_at.desc()).all()

    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "original_size": d.original_size_bytes,
            "compressed_size": d.compressed_size_bytes,
            "storage_path": d.storage_path,
            "created_at": d.created_at.isoformat() if d.created_at else None
        }
        for d in docs
    ]


@router.get("/{document_id}/content")
def get_document_content(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        doc_uuid = uuid.UUID(document_id)
        doc = db.query(Document).filter(Document.id == doc_uuid).first()
    except ValueError:
        doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        binary_data = supabase_admin.storage.from_("compressed_docs").download(doc.storage_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document from cloud storage: {str(e)}")

    try:
        restored_text = decompress_text_huffman(binary_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"C++ Decompression Error: {str(e)}")

    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "original_size": doc.original_size_bytes,
        "compressed_size": doc.compressed_size_bytes,
        "content": restored_text
    }


@router.patch("/{document_id}")
def rename_document(
    document_id: str,
    payload: RenameDocumentRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Updates document filename in database."""
    try:
        doc_uuid = uuid.UUID(document_id)
        doc = db.query(Document).filter(Document.id == doc_uuid).first()
    except ValueError:
        doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not payload.new_filename.strip():
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    doc.filename = payload.new_filename.strip()
    db.commit()

    return {"status": "success", "message": "Document renamed successfully.", "filename": doc.filename}


@router.delete("/{document_id}")
def delete_document(
    document_id: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deletes document record from PostgreSQL and removes binary file from Supabase storage."""
    try:
        doc_uuid = uuid.UUID(document_id)
        doc = db.query(Document).filter(Document.id == doc_uuid).first()
    except ValueError:
        doc = db.query(Document).filter(Document.id == document_id).first()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Remove file from Supabase Storage
    try:
        supabase_admin.storage.from_("compressed_docs").remove([doc.storage_path])
    except Exception as e:
        print(f"⚠️ Storage deletion warning: {str(e)}")

    # Delete row from PostgreSQL database
    db.delete(doc)
    db.commit()

    return {"status": "success", "message": "Document deleted successfully."}