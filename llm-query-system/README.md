# LLM-Powered Intelligent Query-Retrieval System

A sophisticated document analysis system that processes PDFs, DOCX, and email documents to answer natural language queries with contextual decisions and explainable rationale.

## 🚀 Features

- **Multi-format Document Processing**: PDF, DOCX, and email support
- **Semantic Search**: FAISS-powered vector similarity search
- **LLM Integration**: Llama 3 70B for intelligent query understanding and response generation
- **Cross-encoder Reranking**: Improved result relevance using sentence transformers
- **Explainable AI**: Detailed decision rationale with supporting evidence
- **Domain Specialization**: Optimized for insurance, legal, HR, and compliance domains
- **RESTful API**: FastAPI-based endpoints for easy integration
- **Token Optimization**: Efficient LLM usage tracking

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Document      │    │   Embedding      │    │   Vector        │
│   Parser        │───▶│   Service        │───▶│   Search        │
│   (PDF/DOCX)    │    │   (SentenceT)    │    │   (FAISS)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Query         │    │   Reranking      │    │   LLM           │
│   Processing    │◀───│   Service        │◀───│   Service       │
│   Engine        │    │   (Cross-enc)    │    │   (Llama 3)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📋 Requirements

- Python 3.12+
- PostgreSQL (or SQLite for development)
- 16GB+ RAM (for Llama 70B model)
- GPU recommended for LLM inference

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd llm-query-system
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Download spaCy model** (optional, for better text processing):
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

6. **Initialize database**:
   ```bash
   # The database will be created automatically on first run
   mkdir -p data  # For FAISS index storage
   ```

## 🚀 Quick Start

1. **Start the server**:
   ```bash
   ./run_server.py
   ```

2. **Upload a document**:
   ```bash
   curl -X POST "http://localhost:8000/documents" \
        -H "Content-Type: application/json" \
        -d '{
          "document_url": "https://example.com/policy.pdf",
          "document_type": "pdf",
          "domain": "insurance"
        }'
   ```

3. **Query the document**:
   ```bash
   curl -X POST "http://localhost:8000/process-query" \
        -H "Content-Type: application/json" \
        -d '{
          "query": "Does this policy cover knee surgery?",
          "domain": "insurance",
          "max_results": 5
        }'
   ```

## 📝 API Endpoints

### Document Management
- `POST /documents` - Upload document from URL
- `POST /upload-document` - Upload document file
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get document details
- `DELETE /documents/{id}` - Delete document

### Query Processing
- `POST /process-query` - Process natural language query
- `GET /health` - Health check

## 🔧 Configuration

Key configuration options in `.env`:

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# LLM Configuration
LLM_MODEL_NAME=meta-llama/Llama-2-70b-chat-hf
LLM_MAX_TOKENS=4096
LLM_TEMPERATURE=0.1

# Embedding Configuration
EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Vector Search
FAISS_INDEX_PATH=./data/faiss_index
MAX_RETRIEVAL_RESULTS=20
TOP_K_RERANK=5
```

## 📊 Example Query Response

```json
{
  "query_id": "uuid-here",
  "query": "Does this policy cover knee surgery?",
  "answer": "Yes, knee surgery is covered under orthopedic procedures...",
  "decision": "Yes",
  "matched_clauses": [
    {
      "clause_id": "doc_1_chunk_5",
      "clause_text": "Orthopedic procedures including knee surgery...",
      "relevance_score": 0.92,
      "page_number": 3,
      "section": "Coverage Benefits"
    }
  ],
  "rationale": {
    "reasoning": "The policy explicitly covers orthopedic procedures...",
    "supporting_clauses": ["Knee surgery is listed...", "Medical necessity..."],
    "confidence_score": 0.89,
    "key_factors": ["Medical necessity", "Prior authorization"]
  },
  "processing_time_ms": 1245.6
}
```

## 🧪 Testing

Run the example client:
```bash
python examples/example_client.py
```

## 🔍 Supported Domains

- **Insurance**: Policy coverage, exclusions, claims
- **Legal**: Contract analysis, compliance checking
- **HR**: Policy interpretation, benefit queries
- **Compliance**: Regulatory requirement analysis

## 📈 Performance Optimization

- **Token Efficiency**: Optimized prompts and context management
- **Caching**: Vector embeddings cached in FAISS
- **Chunking**: Intelligent text segmentation for better retrieval
- **Reranking**: Cross-encoder improves precision

## 🛡️ Security Considerations

- Input validation on all endpoints
- File size limits for uploads
- SQL injection protection via SQLAlchemy
- Environment variable configuration

## 🐛 Troubleshooting

### Common Issues

1. **Memory Issues with Large Models**:
   - Use model quantization (8-bit/4-bit)
   - Consider using model APIs instead of local inference

2. **spaCy Model Not Found**:
   ```bash
   python -m spacy download en_core_web_sm
   ```

3. **Database Connection Issues**:
   - Check DATABASE_URL in .env
   - Ensure PostgreSQL is running

## 📚 Project Structure

```
llm-query-system/
├── api/                 # FastAPI application
├── core/               # Core services (LLM, embedding, etc.)
├── models/             # Data models (Pydantic, SQLAlchemy)
├── utils/              # Utilities (document parser, database)
├── config/             # Configuration management
├── examples/           # Example usage scripts
├── requirements.txt    # Python dependencies
├── run_server.py      # Server startup script
└── README.md          # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.
