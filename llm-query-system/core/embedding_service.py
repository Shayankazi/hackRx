import os
import json
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import faiss
from config.settings import settings


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.index = None
        self.document_chunks = {}  # Maps index ID to chunk metadata
        self.is_initialized = False
        
    def initialize(self):
        """Initialize the embedding model and FAISS index"""
        if self.is_initialized:
            return
            
        # Load embedding model
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL_NAME}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        
        # Initialize or load FAISS index
        self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)  # Inner product for cosine similarity
        
        # Try to load existing index
        self._load_index()
        
        self.is_initialized = True
        print("Embedding service initialized successfully")
    
    def encode_texts(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts"""
        if not self.is_initialized:
            self.initialize()
            
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings
    
    def encode_query(self, query: str) -> np.ndarray:
        """Generate embedding for a single query"""
        if not self.is_initialized:
            self.initialize()
            
        embedding = self.model.encode([query], normalize_embeddings=True)
        return embedding[0]
    
    def add_documents(self, document_id: str, chunks: List[Dict[str, Any]]) -> List[str]:
        """Add document chunks to the vector index"""
        if not self.is_initialized:
            self.initialize()
        
        chunk_ids = []
        texts = []
        
        for chunk in chunks:
            chunk_id = f"{document_id}_{chunk['chunk_index']}"
            chunk_ids.append(chunk_id)
            texts.append(chunk['text'])
            
            # Store chunk metadata
            self.document_chunks[len(self.document_chunks)] = {
                'chunk_id': chunk_id,
                'document_id': document_id,
                'chunk_index': chunk['chunk_index'],
                'text': chunk['text'],
                'metadata': chunk
            }
        
        # Generate embeddings
        embeddings = self.encode_texts(texts)
        
        # Add to FAISS index
        self.index.add(embeddings.astype('float32'))
        
        print(f"Added {len(chunks)} chunks for document {document_id}")
        return chunk_ids
    
    def search(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search for similar chunks using vector similarity"""
        if not self.is_initialized:
            self.initialize()
            
        top_k = top_k or settings.MAX_RETRIEVAL_RESULTS
        
        # Generate query embedding
        query_embedding = self.encode_query(query)
        query_vector = query_embedding.reshape(1, -1).astype('float32')
        
        # Search in FAISS index
        scores, indices = self.index.search(query_vector, top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx >= 0 and idx < len(self.document_chunks):
                chunk_info = self.document_chunks[idx].copy()
                chunk_info['similarity_score'] = float(score)
                results.append(chunk_info)
        
        return results
    
    def search_by_document(self, query: str, document_id: str, top_k: int = None) -> List[Dict[str, Any]]:
        """Search within a specific document"""
        if not self.is_initialized:
            self.initialize()
            
        # First get all results
        all_results = self.search(query, top_k * 2)  # Get more to filter
        
        # Filter by document ID
        document_results = [
            result for result in all_results 
            if result['document_id'] == document_id
        ]
        
        return document_results[:top_k or settings.MAX_RETRIEVAL_RESULTS]
    
    def get_chunk_by_id(self, chunk_id: str) -> Dict[str, Any]:
        """Retrieve chunk information by ID"""
        for chunk_info in self.document_chunks.values():
            if chunk_info['chunk_id'] == chunk_id:
                return chunk_info
        return None
    
    def remove_document(self, document_id: str):
        """Remove all chunks for a document from the index"""
        # Note: FAISS doesn't support direct deletion, so we'd need to rebuild
        # For now, we'll mark chunks as deleted in metadata
        chunks_to_remove = []
        for idx, chunk_info in self.document_chunks.items():
            if chunk_info['document_id'] == document_id:
                chunk_info['deleted'] = True
                chunks_to_remove.append(idx)
        
        print(f"Marked {len(chunks_to_remove)} chunks as deleted for document {document_id}")
    
    def save_index(self):
        """Save FAISS index and metadata to disk"""
        if not self.is_initialized:
            return
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(settings.FAISS_INDEX_PATH), exist_ok=True)
        
        # Save FAISS index
        faiss.write_index(self.index, f"{settings.FAISS_INDEX_PATH}.faiss")
        
        # Save chunk metadata
        with open(f"{settings.FAISS_INDEX_PATH}_metadata.json", 'w') as f:
            json.dump(self.document_chunks, f, indent=2)
        
        print(f"Index saved to {settings.FAISS_INDEX_PATH}")
    
    def _load_index(self):
        """Load existing FAISS index and metadata"""
        try:
            faiss_path = f"{settings.FAISS_INDEX_PATH}.faiss"
            metadata_path = f"{settings.FAISS_INDEX_PATH}_metadata.json"
            
            if os.path.exists(faiss_path) and os.path.exists(metadata_path):
                # Load FAISS index
                self.index = faiss.read_index(faiss_path)
                
                # Load metadata
                with open(metadata_path, 'r') as f:
                    self.document_chunks = json.load(f)
                    # Convert string keys back to integers
                    self.document_chunks = {int(k): v for k, v in self.document_chunks.items()}
                
                print(f"Loaded existing index with {len(self.document_chunks)} chunks")
            else:
                print("No existing index found, starting fresh")
                
        except Exception as e:
            print(f"Error loading index: {e}, starting fresh")
            self.index = faiss.IndexFlatIP(settings.EMBEDDING_DIMENSION)
            self.document_chunks = {}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector index"""
        if not self.is_initialized:
            return {"status": "not_initialized"}
            
        active_chunks = sum(1 for chunk in self.document_chunks.values() if not chunk.get('deleted', False))
        unique_documents = len(set(
            chunk['document_id'] for chunk in self.document_chunks.values() 
            if not chunk.get('deleted', False)
        ))
        
        return {
            "status": "initialized",
            "total_vectors": self.index.ntotal if self.index else 0,
            "active_chunks": active_chunks,
            "unique_documents": unique_documents,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
            "model_name": settings.EMBEDDING_MODEL_NAME
        }


# Global instance
embedding_service = EmbeddingService()
