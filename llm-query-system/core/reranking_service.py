from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from config.settings import settings


class RerankingService:
    def __init__(self):
        self.model = None
        self.is_initialized = False
    
    def initialize(self):
        """Initialize a sentence transformer model for reranking"""
        if self.is_initialized:
            return
            
        print(f"Loading reranking model: {settings.CROSS_ENCODER_MODEL}")
        # Use a different model for reranking that's available
        try:
            # Try to use a cross-encoder model if available
            from sentence_transformers.cross_encoder import CrossEncoder
            self.model = CrossEncoder(settings.CROSS_ENCODER_MODEL)
            self.model_type = "cross_encoder"
        except ImportError:
            # Fallback to bi-encoder for similarity scoring
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.model_type = "bi_encoder"
            print("Using bi-encoder for reranking (cross-encoder not available)")
        
        self.is_initialized = True
        print("Reranking service initialized successfully")
    
    def rerank_results(self, query: str, search_results: List[Dict[str, Any]], top_k: int = None) -> List[Dict[str, Any]]:
        """Rerank search results using model scores"""
        if not self.is_initialized:
            self.initialize()
        
        if not search_results:
            return []
        
        top_k = top_k or settings.TOP_K_RERANK
        
        if self.model_type == "cross_encoder":
            # Use cross-encoder for direct query-document scoring
            query_doc_pairs = [[query, result['text']] for result in search_results]
            cross_encoder_scores = self.model.predict(query_doc_pairs)
            
            for i, result in enumerate(search_results):
                result['cross_encoder_score'] = float(cross_encoder_scores[i])
                result['combined_score'] = (0.3 * result.get('similarity_score', 0.0) + 
                                          0.7 * result['cross_encoder_score'])
        else:
            # Use bi-encoder for similarity scoring
            query_embedding = self.model.encode([query])
            doc_embeddings = self.model.encode([result['text'] for result in search_results])
            
            # Calculate cosine similarities
            similarities = np.dot(query_embedding, doc_embeddings.T)[0]
            
            for i, result in enumerate(search_results):
                result['cross_encoder_score'] = float(similarities[i])
                result['combined_score'] = (0.5 * result.get('similarity_score', 0.0) + 
                                          0.5 * result['cross_encoder_score'])
        
        # Sort by combined score and return top k
        reranked_results = sorted(search_results, key=lambda x: x['combined_score'], reverse=True)
        return reranked_results[:top_k]
    
    def score_query_document_pair(self, query: str, document_text: str) -> float:
        """Score a single query-document pair"""
        if not self.is_initialized:
            self.initialize()
        
        if self.model_type == "cross_encoder":
            score = self.model.predict([[query, document_text]])
            return float(score[0])
        else:
            query_embedding = self.model.encode([query])
            doc_embedding = self.model.encode([document_text])
            similarity = np.dot(query_embedding, doc_embedding.T)[0][0]
            return float(similarity)
    
    def batch_score(self, query_doc_pairs: List[Tuple[str, str]]) -> List[float]:
        """Score multiple query-document pairs in batch"""
        if not self.is_initialized:
            self.initialize()
        
        if self.model_type == "cross_encoder":
            scores = self.model.predict(query_doc_pairs)
            return [float(score) for score in scores]
        else:
            queries = [pair[0] for pair in query_doc_pairs]
            docs = [pair[1] for pair in query_doc_pairs]
            
            query_embeddings = self.model.encode(queries)
            doc_embeddings = self.model.encode(docs)
            
            similarities = np.sum(query_embeddings * doc_embeddings, axis=1)
            return [float(sim) for sim in similarities]


# Global instance
reranking_service = RerankingService()
