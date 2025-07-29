import uuid
import time
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from models.database import Document, DocumentChunk, Query
from models.schemas import QueryRequest, QueryResponse, ClauseMatch, DecisionRationale, DocumentUploadRequest, DocumentType, Domain
from utils.document_parser import document_parser
from core.embedding_service import embedding_service
from core.reranking_service import reranking_service
from core.llm_service import llm_service


class QueryProcessor:
    def __init__(self, db: Session):
        self.db = db

    def process_query(self, query_request: QueryRequest) -> QueryResponse:
        start_time = time.time()
        query_id = str(uuid.uuid4())

        # Extract structured query
        structured_query = llm_service.extract_structured_query(
            natural_query=query_request.query, domain=query_request.domain.name if query_request.domain else None
        )

        # Perform vector search for relevant chunks
        document_results = embedding_service.search_by_document(
            query=query_request.query, document_id=query_request.document_id, top_k=query_request.max_results
        ) if query_request.document_id else embedding_service.search(
            query=query_request.query, top_k=query_request.max_results
        )

        # Rerank results
        reranked_results = reranking_service.rerank_results(
            query=query_request.query, search_results=document_results, top_k=query_request.max_results
        )

        # Generate query response
        response_data = llm_service.generate_answer(
            query=query_request.query, relevant_chunks=reranked_results, domain=query_request.domain.name if query_request.domain else None
        )

        # Create ClauseMatch objects
        matched_clauses = [
            ClauseMatch(
                clause_id=chunk['chunk_id'],
                clause_text=chunk['text'],
                relevance_score=chunk['combined_score'],
                page_number=chunk['metadata'].get('page_number'),
                section=chunk['metadata'].get('section')
            )
            for chunk in reranked_results
        ]

        # Assemble DecisionRationale
        rationale = DecisionRationale(
            reasoning=response_data['reasoning'],
            supporting_clauses=response_data['supporting_evidence'],
            conflicting_clauses=response_data.get('conflicting_evidence', []),
            confidence_score=response_data['confidence'],
            key_factors=response_data['key_factors']
        )

        # Formulate QueryResponse
        response = QueryResponse(
            query_id=query_id,
            query=query_request.query,
            answer=response_data['answer'],
            decision=response_data.get('decision'),
            matched_clauses=matched_clauses,
            rationale=rationale,
            processing_time_ms=(time.time() - start_time) * 1000,
            token_usage=response_data.get('token_usage')
        )

        # Store query in database
        self.store_query_in_db(query_id, query_request, response)

        return response

    def store_query_in_db(self, query_id: str, query_request: QueryRequest, response: QueryResponse):
        # Convert response to dict with datetime serialization
        response_dict = response.dict()
        # Convert datetime to ISO string
        if 'timestamp' in response_dict and response_dict['timestamp']:
            response_dict['timestamp'] = response_dict['timestamp'].isoformat()
        
        query_record = Query(
            id=query_id,
            query_text=query_request.query,
            document_id=query_request.document_id,
            domain=query_request.domain.name if query_request.domain else None,
            response_data=response_dict,
            processing_time_ms=response.processing_time_ms,
            token_usage=response.token_usage
        )
        self.db.add(query_record)
        self.db.commit()
    
    async def process_document_and_questions(self, document_url: str, questions: List[str]) -> List[str]:
        """Process a document from URL and answer multiple questions"""
        try:
            # Create document upload request
            upload_request = DocumentUploadRequest(
                document_url=document_url,
                document_type=DocumentType.PDF,  # Assuming PDF for now
                domain=Domain.INSURANCE,  # Assuming insurance domain
                metadata={"filename": "hackrx_document.pdf"}
            )
            
            # Import document service (avoid circular import)
            from core.document_service import DocumentService
            doc_service = DocumentService(self.db)
            
            # Process the document
            doc_info = await doc_service.process_document(upload_request)
            
            # Process each question
            answers = []
            for question in questions:
                query_request = QueryRequest(
                    query=question,
                    document_id=doc_info.document_id,
                    domain=Domain.INSURANCE,
                    max_results=5
                )
                
                response = self.process_query(query_request)
                answers.append(response.answer)
            
            return answers
            
        except Exception as e:
            raise Exception(f"Error processing document and questions: {str(e)}")

