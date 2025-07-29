# HackRX LLM Query-Retrieval System

## Overview

This is a complete implementation of an LLM-powered document query and retrieval system that specifically handles the HackRX API requirements. The system can:

1. Download and process PDF documents from URLs
2. Chunk documents intelligently using spaCy
3. Create vector embeddings using sentence transformers
4. Answer multiple questions about the document content
5. Return structured responses matching the HackRX format

## API Endpoints

### HackRX Main Endpoint
- **POST** `/hackrx/run`
- **Request Format:**
```json
{
    "documents": "https://hackrx.blob.core.windows.net/assets/policy.pdf?sv=...",
    "questions": [
        "What is the grace period for premium payment?",
        "What is the waiting period for pre-existing diseases?"
    ]
}
```

- **Response Format:**
```json
{
    "answers": [
        "Based on the most relevant document section, ...",
        "Based on the most relevant document section, ..."
    ]
}
```

### Health Check
- **GET** `/health`
- Returns system status and service health

## System Architecture

### Core Components

1. **Document Service** (`core/document_service.py`)
   - Downloads PDFs from URLs
   - Parses documents using pdfplumber
   - Chunks text intelligently
   - Manages document storage and metadata

2. **Embedding Service** (`core/embedding_service.py`)
   - Generates vector embeddings using sentence-transformers
   - Manages FAISS vector index
   - Performs semantic search

3. **Query Processor** (`core/query_processor.py`)
   - Orchestrates the query pipeline
   - Handles HackRX workflow
   - Manages database operations

4. **LLM Service** (`core/llm_service.py`)
   - Generates answers using language models
   - Fallback to rule-based processing
   - Extracts structured information

5. **Reranking Service** (`core/reranking_service.py`)
   - Re-ranks search results using cross-encoders
   - Improves relevance scoring

### Database Schema

- **Documents**: Stores document metadata and processing status
- **Document Chunks**: Stores chunked text content with metadata
- **Queries**: Logs all queries and responses
- **Clause Index**: Indexes key clauses and terms

## Installation & Setup

### Prerequisites
```bash
python -m pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Configuration
The system uses SQLite by default but can be configured for PostgreSQL:
```python
# config/settings.py
DATABASE_URL = "sqlite:///./data/llm_query_db.sqlite"
```

### Running the Server
```bash
python run_server.py
```
Server runs on: `http://localhost:8002`

## Testing

### Health Check
```bash
curl http://localhost:8002/health
```

### HackRX Endpoint Test
```bash
python test_hackrx.py
```

### Simple Test
```bash
python simple_test.py
```

## Key Features

### 1. Document Processing
- **Multi-format Support**: PDF, DOCX, Email
- **Smart Chunking**: Uses spaCy for sentence-aware chunking
- **Metadata Extraction**: Page numbers, sections, key phrases
- **Async Processing**: Non-blocking document downloads

### 2. Vector Search
- **FAISS Integration**: Fast similarity search
- **Embedding Models**: sentence-transformers/all-MiniLM-L6-v2
- **Persistent Storage**: Index saved to disk
- **Incremental Updates**: Add/remove documents dynamically

### 3. Query Processing
- **Semantic Search**: Vector-based document retrieval
- **Reranking**: Cross-encoder reranking for better relevance
- **Fallbacks**: Rule-based processing when LLM unavailable
- **Structured Responses**: Consistent JSON output

### 4. Error Handling
- **Graceful Degradation**: Falls back to rule-based when models fail
- **Timeout Management**: Handles long-running requests
- **Database Resilience**: Transaction rollbacks on errors
- **Logging**: Comprehensive error logging

## Performance Optimizations

1. **Model Loading**: Lazy initialization of heavy models
2. **Caching**: Vector index persisted between sessions
3. **Batching**: Efficient batch processing of embeddings
4. **Memory Management**: 8-bit quantization for LLMs
5. **Connection Pooling**: Database connection management

## API Response Examples

### Successful Response
```json
{
  "answers": [
    "A grace period of thirty days is provided for premium payment after the due date to renew or continue the policy without losing continuity benefits.",
    "There is a waiting period of thirty-six (36) months of continuous coverage from the first policy inception for pre-existing diseases and their direct complications to be covered."
  ]
}
```

### Error Response
```json
{
  "detail": "Error processing request: Document URL is not accessible"
}
```

## Troubleshooting

### Common Issues

1. **Model Loading Errors**
   - Install bitsandbytes: `pip install -U bitsandbytes`
   - Use smaller models for testing

2. **Memory Issues**
   - Reduce chunk size in settings
   - Use quantization for large models

3. **Network Timeouts**
   - Increase timeout values
   - Check document URL accessibility

4. **Database Errors**
   - Ensure data directory exists
   - Check file permissions

## Production Considerations

1. **Scalability**: Use PostgreSQL and Redis for production
2. **Security**: Add authentication and rate limiting
3. **Monitoring**: Implement comprehensive logging
4. **Caching**: Add document and query result caching
5. **Load Balancing**: Deploy multiple instances

## File Structure
```
llm-query-system/
├── api/
│   └── main.py              # FastAPI application
├── core/
│   ├── document_service.py  # Document processing
│   ├── embedding_service.py # Vector embeddings
│   ├── llm_service.py      # Language model integration
│   ├── query_processor.py  # Query orchestration
│   └── reranking_service.py # Result reranking
├── models/
│   ├── database.py         # SQLAlchemy models
│   └── schemas.py          # Pydantic schemas
├── utils/
│   ├── database.py         # Database utilities
│   └── document_parser.py  # Document parsing
├── config/
│   └── settings.py         # Configuration
├── data/                   # Data storage
├── requirements.txt        # Dependencies
├── run_server.py          # Server startup
└── test_hackrx.py         # Testing script
```

## Model Configuration

The system supports various models:

- **Embeddings**: sentence-transformers models
- **LLM**: Hugging Face transformers or API-based
- **Cross-encoder**: For reranking
- **NLP**: spaCy for text processing

## License

This project is built for the HackRX competition and demonstrates enterprise-grade document query capabilities.
