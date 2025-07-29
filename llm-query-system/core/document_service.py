import uuid
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import Document, DocumentChunk, ClauseIndex
from models.schemas import DocumentType, Domain, DocumentUploadRequest, DocumentInfo
from utils.document_parser import document_parser
from core.embedding_service import embedding_service
from core.llm_service import llm_service


class DocumentService:
    def __init__(self, db: Session):
        self.db = db
    
    async def process_document(self, upload_request: DocumentUploadRequest, file_content: bytes = None) -> DocumentInfo:
        """Process and index a document"""
        document_id = str(uuid.uuid4())
        
        try:
            # Download or use provided file content
            if upload_request.document_url:
                temp_file_path = await document_parser.download_document(upload_request.document_url)
            else:
                # Save uploaded file content to temporary file
                import tempfile
                suffix = self._get_file_extension(upload_request.document_type)
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_file.write(file_content)
                temp_file.close()
                temp_file_path = temp_file.name
            
            # Parse document
            full_text, metadata = await document_parser.parse_document(
                temp_file_path, upload_request.document_type
            )
            
            # Create document record
            document_record = Document(
                id=document_id,
                filename=upload_request.metadata.get('filename', f'document_{document_id}'),
                document_type=upload_request.document_type.value,
                domain=upload_request.domain.value if upload_request.domain else None,
                original_url=upload_request.document_url,
                file_path=temp_file_path,
                processing_status="processing",
                document_metadata=upload_request.metadata
            )
            
            self.db.add(document_record)
            self.db.commit()
            
            # Chunk the document
            chunks = document_parser.chunk_text(full_text)
            
            # Process and store chunks
            chunk_records = []
            for chunk in chunks:
                chunk_id = f"{document_id}_{chunk['chunk_index']}"
                
                # Extract metadata for the chunk (page numbers, sections, etc.)
                chunk_metadata = self._extract_chunk_metadata(chunk, metadata)
                
                chunk_record = DocumentChunk(
                    id=chunk_id,
                    document_id=document_id,
                    chunk_index=chunk['chunk_index'],
                    text_content=chunk['text'],
                    page_number=chunk_metadata.get('page_number'),
                    section=chunk_metadata.get('section'),
                    chunk_metadata=chunk_metadata
                )
                
                chunk_records.append(chunk_record)
                self.db.add(chunk_record)
            
            # Add chunks to vector index
            embedding_service.add_documents(document_id, chunks)
            
            # Extract and index key clauses
            await self._extract_and_index_clauses(document_id, chunks, upload_request.domain)
            
            # Update document status
            document_record.processing_status = "completed"
            document_record.total_chunks = len(chunks)
            self.db.commit()
            
            # Save vector index
            embedding_service.save_index()
            
            # Clean up temporary file
            document_parser.cleanup_temp_file(temp_file_path)
            
            return DocumentInfo(
                document_id=document_id,
                filename=document_record.filename,
                document_type=DocumentType(document_record.document_type),
                domain=Domain(document_record.domain) if document_record.domain else None,
                upload_timestamp=document_record.created_at,
                processing_status=document_record.processing_status,
                total_chunks=document_record.total_chunks,
                metadata=document_record.document_metadata
            )
            
        except Exception as e:
            # Update document status to failed
            if 'document_record' in locals():
                document_record.processing_status = "failed"
                document_record.document_metadata = {**document_record.document_metadata, "error": str(e)}
                self.db.commit()
            
            raise e
    
    def _get_file_extension(self, document_type: DocumentType) -> str:
        """Get appropriate file extension for document type"""
        extensions = {
            DocumentType.PDF: ".pdf",
            DocumentType.DOCX: ".docx",
            DocumentType.EMAIL: ".eml"
        }
        return extensions.get(document_type, ".txt")
    
    def _extract_chunk_metadata(self, chunk: Dict[str, Any], document_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata for a specific chunk"""
        # This is a simplified version - in practice, you'd need more sophisticated
        # logic to map chunks to pages/sections based on the original document structure
        
        chunk_metadata = {
            "word_count": chunk.get('word_count', 0),
            "char_count": chunk.get('char_count', 0),
            "chunk_index": chunk.get('chunk_index', 0)
        }
        
        # Try to determine page number based on chunk position
        if document_metadata.get('pages'):
            total_pages = document_metadata.get('total_pages', 1)
            estimated_page = min(
                int((chunk['chunk_index'] / 10) * total_pages) + 1,  # Rough estimation
                total_pages
            )
            chunk_metadata['page_number'] = estimated_page
        
        # Extract key phrases for this chunk
        key_phrases = document_parser.extract_key_phrases(chunk['text'])
        chunk_metadata['key_phrases'] = key_phrases[:10]  # Limit to top 10
        
        return chunk_metadata
    
    async def _extract_and_index_clauses(self, document_id: str, chunks: List[Dict[str, Any]], domain: Optional[Domain]):
        """Extract and index key clauses from document chunks"""
        for chunk in chunks:
            # Extract clauses using LLM service
            clauses = llm_service.extract_key_clauses(
                chunk['text'], 
                domain.value if domain else None
            )
            
            for clause in clauses:
                clause_record = ClauseIndex(
                    id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_id=f"{document_id}_{chunk['chunk_index']}",
                    clause_type=clause['type'],
                    clause_summary=clause['text'][:500],  # Truncate for storage
                    key_terms=document_parser.extract_key_phrases(clause['text']),
                    relevance_score=clause['importance']
                )
                
                self.db.add(clause_record)
        
        self.db.commit()
    
    def get_document_info(self, document_id: str) -> Optional[DocumentInfo]:
        """Retrieve document information"""
        document = self.db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            return None
        
        return DocumentInfo(
            document_id=document.id,
            filename=document.filename,
            document_type=DocumentType(document.document_type),
            domain=Domain(document.domain) if document.domain else None,
            upload_timestamp=document.created_at,
            processing_status=document.processing_status,
            total_chunks=document.total_chunks,
            metadata=document.document_metadata
        )
    
    def list_documents(self, domain: Optional[Domain] = None, limit: int = 50) -> List[DocumentInfo]:
        """List all documents, optionally filtered by domain"""
        query = self.db.query(Document)
        
        if domain:
            query = query.filter(Document.domain == domain.value)
        
        documents = query.limit(limit).all()
        
        return [
            DocumentInfo(
                document_id=doc.id,
                filename=doc.filename,
                document_type=DocumentType(doc.document_type),
                domain=Domain(doc.domain) if doc.domain else None,
                upload_timestamp=doc.created_at,
                processing_status=doc.processing_status,
                total_chunks=doc.total_chunks,
                metadata=doc.document_metadata
            )
            for doc in documents
        ]
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its associated data"""
        try:
            # Remove from vector index
            embedding_service.remove_document(document_id)
            
            # Delete from database
            self.db.query(ClauseIndex).filter(ClauseIndex.document_id == document_id).delete()
            self.db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).delete()
            document = self.db.query(Document).filter(Document.id == document_id).first()
            
            if document:
                # Clean up file if it exists
                if document.file_path and os.path.exists(document.file_path):
                    os.unlink(document.file_path)
                
                self.db.delete(document)
                self.db.commit()
                
                # Save updated vector index
                embedding_service.save_index()
                
                return True
            
            return False
            
        except Exception as e:
            self.db.rollback()
            print(f"Error deleting document {document_id}: {e}")
            return False
    
    def get_document_chunks(self, document_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve chunks for a specific document"""
        chunks = self.db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).limit(limit).all()
        
        return [
            {
                "chunk_id": chunk.id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text_content,
                "page_number": chunk.page_number,
                "section": chunk.section,
                "metadata": chunk.chunk_metadata
            }
            for chunk in chunks
        ]
