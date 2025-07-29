from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from models.schemas import HealthCheck, DocumentUploadRequest, QueryRequest, QueryResponse, DocumentInfo, Domain, HackRxRequest, HackRxResponse
from utils.database import get_db
from core.document_service import DocumentService
from core.query_processor import QueryProcessor
from datetime import datetime
from config.settings import settings


app = FastAPI(title=settings.API_TITLE, version=settings.API_VERSION)


document_service: DocumentService = None  # Will be initialized with db
document_processor: QueryProcessor = None  # Will be initialized with db


def init_services(db: Session):
    global document_service, document_processor
    document_service = DocumentService(db)
    document_processor = QueryProcessor(db)


@app.on_event("startup")
async def startup_event():
    init_services(next(get_db()))


@app.get("/health", response_model=HealthCheck)
def health_check():
    # Simulated service statuses, can be replaced with actual checks
    services = {
        "database": "ok",
        "embedding_service": "ok",
        "LLM_service": "ok",
        "vector_search": "ok"
    }
    
    return HealthCheck(status="healthy", timestamp=datetime.utcnow(), version=settings.API_VERSION, services=services)


@app.post("/hackrx/run", response_model=HackRxResponse)
async def hackrx_run(request: HackRxRequest, db: Session = Depends(get_db)):
    """HackRx endpoint to process document and answer questions"""
    try:
        # Process document and answer questions
        answers = await document_processor.process_document_and_questions(
            request.documents, request.questions
        )
        
        return HackRxResponse(answers=answers)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")


@app.post("/upload-document", response_model=DocumentInfo)
async def upload_document(upload_request: DocumentUploadRequest, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Handle document upload and processing"""
    file_content = await file.read()
    doc_info = await document_service.process_document(upload_request, file_content)
    return doc_info


@app.post("/process-query", response_model=QueryResponse)
async def process_query(query_request: QueryRequest, db: Session = Depends(get_db)):
    """Handle query processing and return answer and decision rationale"""
    response = document_processor.process_query(query_request)
    return response


@app.get("/documents", response_model=List[DocumentInfo])
def list_documents(domain: str = None, db: Session = Depends(get_db)):
    """List available documents"""
    domain_enum = Domain(domain) if domain else None
    return document_service.list_documents(domain_enum) 


@app.get("/documents/{document_id}", response_model=DocumentInfo)
def get_document(document_id: str, db: Session = Depends(get_db)):
    """Get information about a specific document"""
    doc_info = document_service.get_document_info(document_id)
    if not doc_info:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc_info


@app.delete("/documents/{document_id}", response_model=bool)
def delete_document(document_id: str, db: Session = Depends(get_db)):
    """Delete a document and its associated data"""
    success = document_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found or could not be deleted")
    return True


@app.get("/documents/{document_id}/chunks", response_model=List[Dict[str, Any]])
def get_document_chunks(document_id: str, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieve document chunks"""
    return document_service.get_document_chunks(document_id, limit) 


@app.post("/documents", response_model=DocumentInfo)
async def process_document_upload(document_request: DocumentUploadRequest, db: Session = Depends(get_db)):
    """Process document uploads"""
    document_info = await document_service.process_document(document_request)
    return document_info
