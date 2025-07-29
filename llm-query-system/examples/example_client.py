#!/usr/bin/env python3

import requests
import json
import time
from typing import Dict, Any

# Base API URL
BASE_URL = "http://localhost:8000"

class LLMQueryClient:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        return response.json()
    
    def upload_document_url(self, document_url: str, document_type: str, domain: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload document from URL"""
        payload = {
            "document_url": document_url,
            "document_type": document_type,
            "domain": domain,
            "metadata": metadata or {}
        }
        
        response = self.session.post(f"{self.base_url}/documents", json=payload)
        return response.json()
    
    def upload_document_file(self, file_path: str, document_type: str, domain: str = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Upload document file"""
        upload_data = {
            "document_type": document_type,
            "domain": domain,
            "metadata": metadata or {"filename": file_path.split("/")[-1]}
        }
        
        with open(file_path, 'rb') as file:
            files = {"file": file}
            data = {"upload_request": json.dumps(upload_data)}
            response = self.session.post(f"{self.base_url}/upload-document", files=files, data=data)
        
        return response.json()
    
    def query_documents(self, query: str, document_id: str = None, domain: str = None, max_results: int = 5) -> Dict[str, Any]:
        """Query documents"""
        payload = {
            "query": query,
            "document_id": document_id,
            "domain": domain,
            "max_results": max_results
        }
        
        response = self.session.post(f"{self.base_url}/process-query", json=payload)
        return response.json()
    
    def list_documents(self, domain: str = None) -> Dict[str, Any]:
        """List all documents"""
        params = {"domain": domain} if domain else {}
        response = self.session.get(f"{self.base_url}/documents", params=params)
        return response.json()
    
    def get_document(self, document_id: str) -> Dict[str, Any]:
        """Get document information"""
        response = self.session.get(f"{self.base_url}/documents/{document_id}")
        return response.json()
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document"""
        response = self.session.delete(f"{self.base_url}/documents/{document_id}")
        return response.json()


def main():
    """Example usage of the LLM Query System"""
    client = LLMQueryClient()
    
    # 1. Check API health
    print("1. Checking API health...")
    health = client.health_check()
    print(f"API Status: {health['status']}")
    print()
    
    # 2. Example: Upload a document (simulated)
    print("2. Uploading a sample insurance policy document...")
    
    # This would typically be a real document URL or file
    sample_doc_response = {
        "document_id": "sample-123",
        "filename": "sample_insurance_policy.pdf",
        "document_type": "pdf",
        "domain": "insurance",
        "upload_timestamp": "2024-01-01T00:00:00Z",
        "processing_status": "completed",
        "total_chunks": 25,
        "metadata": {"pages": 10, "size": "2.3MB"}
    }
    
    print(f"Document uploaded: {sample_doc_response['document_id']}")
    print(f"Processing status: {sample_doc_response['processing_status']}")
    print()
    
    # 3. Example: Query the documents
    print("3. Querying: 'Does this policy cover knee surgery, and what are the conditions?'")
    
    # Simulate a query response
    sample_query_response = {
        "query_id": "query-456",
        "query": "Does this policy cover knee surgery, and what are the conditions?",
        "answer": "Yes, this policy covers knee surgery under the orthopedic procedures benefit. The conditions include: 1) Prior authorization from your primary care physician, 2) The surgery must be deemed medically necessary, 3) A 30-day waiting period applies for elective procedures.",
        "decision": "Yes",
        "matched_clauses": [
            {
                "clause_id": "sample-123_5",
                "clause_text": "Orthopedic procedures, including knee surgery, are covered when medically necessary and pre-authorized by the attending physician.",
                "relevance_score": 0.92,
                "page_number": 3,
                "section": "Coverage Benefits"
            },
            {
                "clause_id": "sample-123_12",
                "clause_text": "All elective surgical procedures require a 30-day waiting period from the policy effective date.",
                "relevance_score": 0.78,
                "page_number": 7,
                "section": "Waiting Periods"
            }
        ],
        "rationale": {
            "reasoning": "The policy explicitly covers orthopedic procedures including knee surgery under the medical benefits section. However, several conditions must be met including prior authorization and waiting periods for elective procedures.",
            "supporting_clauses": [
                "Orthopedic procedures, including knee surgery, are covered when medically necessary",
                "Prior authorization required from attending physician"
            ],
            "conflicting_clauses": [],
            "confidence_score": 0.89,
            "key_factors": [
                "Medical necessity requirement",
                "Prior authorization requirement",
                "Waiting period for elective procedures"
            ]
        },
        "processing_time_ms": 1245.6,
        "timestamp": "2024-01-01T12:00:00Z",
        "token_usage": {"total_tokens": 892}
    }
    
    print(f"Answer: {sample_query_response['answer']}")
    print(f"Decision: {sample_query_response['decision']}")
    print(f"Confidence: {sample_query_response['rationale']['confidence_score']:.2f}")
    print(f"Processing time: {sample_query_response['processing_time_ms']:.1f}ms")
    print()
    
    # 4. Show matched clauses
    print("4. Matched clauses:")
    for clause in sample_query_response['matched_clauses']:
        print(f"   - Relevance: {clause['relevance_score']:.2f}")
        print(f"     Page: {clause['page_number']}, Section: {clause['section']}")
        print(f"     Text: {clause['clause_text'][:100]}...")
        print()
    
    # 5. Show reasoning
    print("5. Decision rationale:")
    rationale = sample_query_response['rationale']
    print(f"   Reasoning: {rationale['reasoning']}")
    print(f"   Key factors: {', '.join(rationale['key_factors'])}")
    print()
    
    print("Example completed!")


if __name__ == "__main__":
    main()
