from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.document import Document, ExtractedFinancialData
from app.models.user import User
from app.schemas.documents import DocumentResponse
from app.services.document_processing import DocumentProcessingUnavailable, extract_fields
from app.services.storage import DocumentStorageError, storage

router = APIRouter(prefix='/documents', tags=['documents'])

MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {'application/pdf', 'image/png', 'image/jpeg'}

@router.post('/upload', response_model=DocumentResponse, status_code=status.HTTP_201_CREATED, responses={422: {'description': 'Document could not be processed'}})
async def upload_document(file: Annotated[UploadFile, File(...)], db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    suffix = Path(file.filename or '').suffix.lower()
    if file.content_type not in ALLOWED_TYPES or suffix not in {'.pdf', '.png', '.jpg', '.jpeg'}:
        raise HTTPException(415, 'Only PDF, PNG, and JPEG documents are supported')
    content = await file.read(MAX_FILE_SIZE + 1)
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, 'Document must be 10 MB or smaller')
    document = Document(user_id=user.id, filename=file.filename or 'document', content_type=file.content_type, size_bytes=len(content), storage_key='pending', status='processing')
    db.add(document); db.flush()
    try:
        with TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / f'upload{suffix}'
            path.write_bytes(content)
            extracted = extract_fields(str(path))
    except DocumentProcessingUnavailable as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from exc
    except (ValueError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except OSError as exc:
        db.rollback()
        raise HTTPException(503, 'Document processing storage is unavailable.') from exc

    try:
        document.storage_key = storage.save(content, document.filename, document.content_type)
        document.status = 'needs_review' if extracted['requires_user_verification'] else 'processed'
        db.add(ExtractedFinancialData(document_id=document.id, normalized_data=extracted['fields'], raw_text=extracted['raw_text'], missing_fields=extracted['missing_fields'], validation_errors=extracted['validation_errors'], requires_user_verification=extracted['requires_user_verification']))
        db.commit(); db.refresh(document)
        return {'id': document.id, 'filename': document.filename, 'content_type': document.content_type, 'size_bytes': document.size_bytes, 'status': document.status, 'storage_key': document.storage_key, 'created_at': document.created_at, 'extracted_data': extracted}
    except DocumentStorageError as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from exc
    except OSError as exc:
        db.rollback()
        raise HTTPException(503, 'Document storage is unavailable.') from exc

@router.get('', response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    documents = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    return [
        {
            'id': document.id,
            'filename': document.filename,
            'content_type': document.content_type,
            'size_bytes': document.size_bytes,
            'status': document.status,
            'storage_key': document.storage_key,
            'created_at': document.created_at,
            'extracted_data': {
                'fields': document.extracted_data.normalized_data,
                'missing_fields': document.extracted_data.missing_fields,
                'validation_errors': document.extracted_data.validation_errors,
                'requires_user_verification': document.extracted_data.requires_user_verification,
            } if document.extracted_data else None,
        }
        for document in documents
    ]
