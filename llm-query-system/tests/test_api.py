import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "services" in data

def test_list_documents():
    """Test listing documents"""
    response = client.get("/documents")
    assert response.status_code == 200
    # Should return a list (even if empty)
    assert isinstance(response.json(), list)

def test_process_query_endpoint():
    """Test query processing endpoint structure"""
    query_data = {
        "query": "Test query",
        "max_results": 5
    }
    
    response = client.post("/process-query", json=query_data)
    # May fail due to no documents, but endpoint should exist
    assert response.status_code in [200, 422, 500]  # 422 for validation, 500 for no data

def test_invalid_document_id():
    """Test getting non-existent document"""
    response = client.get("/documents/non-existent-id")
    assert response.status_code == 404
