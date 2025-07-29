import json
import re
from typing import List, Dict, Any, Optional, Tuple
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from config.settings import settings


class LLMService:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self.is_initialized = False
        
    def initialize(self):
        """Initialize the LLM model"""
        if self.is_initialized:
            return
        
        print(f"Loading LLM model: {settings.LLM_MODEL_NAME}")
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(settings.LLM_MODEL_NAME)
        
        # For large models like Llama 70B, you might want to use quantization or other optimizations
        # This is a simplified version - in production, you'd likely use vLLM, TGI, or similar
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                settings.LLM_MODEL_NAME,
                torch_dtype=torch.float16,
                device_map="auto",
                load_in_8bit=True  # Use 8-bit quantization to reduce memory usage
            )
            
            self.pipeline = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=settings.LLM_MAX_TOKENS,
                temperature=settings.LLM_TEMPERATURE,
                do_sample=True,
                return_full_text=False
            )
            
        except Exception as e:
            print(f"Error loading full model: {e}")
            print("Falling back to API-based approach or smaller model")
            # In production, you might use an API endpoint instead
            self.pipeline = None
        
        self.is_initialized = True
        print("LLM service initialized successfully")
    
    def extract_structured_query(self, natural_query: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Extract structured information from natural language query"""
        if not self.is_initialized:
            self.initialize()
        
        domain_context = f" in the {domain} domain" if domain else ""
        
        prompt = f"""
You are an expert document analysis assistant. Extract structured information from the following natural language query{domain_context}.

Query: "{natural_query}"

Please provide a JSON response with the following structure:
{{
    "intent": "coverage_check|exclusion_check|condition_check|general_inquiry",
    "subject": "the main subject or entity being asked about",
    "keywords": ["key", "terms", "to", "search"],
    "question_type": "yes_no|conditional|explanatory",
    "entities": ["specific", "named", "entities"],
    "context_clues": ["additional", "context", "information"]
}}

Response:
"""
        
        try:
            if self.pipeline:
                response = self.pipeline(prompt)[0]['generated_text']
                # Extract JSON from response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    return self._rule_based_extraction(natural_query, domain)
            else:
                # Fallback to rule-based extraction
                return self._rule_based_extraction(natural_query, domain)
                
        except Exception as e:
            print(f"Error in structured query extraction: {e}")
            return self._rule_based_extraction(natural_query, domain)
    
    def _rule_based_extraction(self, query: str, domain: Optional[str] = None) -> Dict[str, Any]:
        """Fallback rule-based query structure extraction"""
        query_lower = query.lower()
        
        # Determine intent
        intent = "general_inquiry"
        if any(word in query_lower for word in ["cover", "covered", "coverage"]):
            intent = "coverage_check"
        elif any(word in query_lower for word in ["exclude", "excluded", "exclusion"]):
            intent = "exclusion_check"
        elif any(word in query_lower for word in ["condition", "requirement", "prerequisite"]):
            intent = "condition_check"
        
        # Determine question type
        question_type = "explanatory"
        if query_lower.startswith(("does", "is", "can", "will", "would")):
            question_type = "yes_no"
        elif any(word in query_lower for word in ["if", "when", "under what"]):
            question_type = "conditional"
        
        # Extract keywords (simple approach)
        keywords = [word for word in query.split() if len(word) > 3 and word.lower() not in 
                   ["does", "this", "what", "are", "the", "conditions", "coverage", "policy"]]
        
        return {
            "intent": intent,
            "subject": query[:50] + "..." if len(query) > 50 else query,
            "keywords": keywords[:10],  # Limit to top 10
            "question_type": question_type,
            "entities": [],  # Would need NER for proper extraction
            "context_clues": [domain] if domain else []
        }
    
    def generate_answer(self, query: str, relevant_chunks: List[Dict[str, Any]], 
                       domain: Optional[str] = None) -> Dict[str, Any]:
        """Generate answer and decision based on query and relevant document chunks"""
        if not self.is_initialized:
            self.initialize()
        
        # Prepare context from relevant chunks
        context = self._prepare_context(relevant_chunks)
        domain_context = f" This is in the {domain} domain." if domain else ""
        
        prompt = f"""
You are an expert document analyst. Based on the provided document excerpts, answer the user's question with high accuracy and provide clear reasoning.{domain_context}

Question: {query}

Document Excerpts:
{context}

Please provide a comprehensive JSON response with:
{{
    "answer": "Direct answer to the question",
    "decision": "Yes/No/Partial/Unclear (if applicable)",
    "confidence": 0.85,
    "reasoning": "Detailed explanation of how you arrived at this answer",
    "supporting_evidence": ["List of key phrases or clauses that support the answer"],
    "conflicting_evidence": ["Any contradictory information found"],
    "key_factors": ["Important factors that influenced the decision"],
    "limitations": ["Any limitations or assumptions in the analysis"]
}}

Response:
"""
        
        try:
            if self.pipeline:
                response = self.pipeline(prompt)[0]['generated_text']
                # Count tokens for usage tracking
                token_count = len(self.tokenizer.encode(prompt + response))
            else:
                response = self._rule_based_answer_generation(query, relevant_chunks, domain)
                token_count = 0
            
            # Extract JSON from response
            if isinstance(response, str):
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    result['token_usage'] = {'total_tokens': token_count}
                    return result
            
            # If no JSON found or response is not string, use rule-based approach
            return self._rule_based_answer_generation(query, relevant_chunks, domain)
                
        except Exception as e:
            print(f"Error in answer generation: {e}")
            return self._rule_based_answer_generation(query, relevant_chunks, domain)
    
    def _prepare_context(self, chunks: List[Dict[str, Any]]) -> str:
        """Prepare context string from document chunks"""
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            chunk_text = chunk.get('text', '')
            score = chunk.get('combined_score', chunk.get('similarity_score', 0))
            context_parts.append(f"[{i}] (Relevance: {score:.3f}) {chunk_text[:500]}...")
        
        return "\n\n".join(context_parts)
    
    def _rule_based_answer_generation(self, query: str, relevant_chunks: List[Dict[str, Any]], 
                                    domain: Optional[str] = None) -> Dict[str, Any]:
        """Fallback rule-based answer generation"""
        if not relevant_chunks:
            return {
                "answer": "I couldn't find relevant information to answer your question.",
                "decision": "Unclear",
                "confidence": 0.1,
                "reasoning": "No relevant document excerpts found for the query.",
                "supporting_evidence": [],
                "conflicting_evidence": [],
                "key_factors": ["Insufficient information"],
                "limitations": ["No relevant documents found"],
                "token_usage": {"total_tokens": 0}
            }
        
        # Simple keyword matching for basic coverage questions
        query_lower = query.lower()
        best_chunk = relevant_chunks[0]
        chunk_text_lower = best_chunk.get('text', '').lower()
        
        # Basic decision logic
        decision = "Unclear"
        confidence = best_chunk.get('combined_score', 0.5)
        
        if "cover" in query_lower:
            if any(word in chunk_text_lower for word in ["covered", "includes", "benefits"]):
                decision = "Yes"
            elif any(word in chunk_text_lower for word in ["excluded", "not covered", "exceptions"]):
                decision = "No"
        
        return {
            "answer": f"Based on the most relevant document section, {best_chunk.get('text', '')[:200]}...",
            "decision": decision,
            "confidence": min(confidence, 0.7),  # Cap confidence for rule-based approach
            "reasoning": "Answer generated based on keyword matching and document similarity.",
            "supporting_evidence": [best_chunk.get('text', '')[:100] + "..."],
            "conflicting_evidence": [],
            "key_factors": ["Document similarity score", "Keyword matching"],
            "limitations": ["Rule-based analysis", "Limited context understanding"],
            "token_usage": {"total_tokens": 0}
        }
    
    def extract_key_clauses(self, text: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """Extract and classify key clauses from document text"""
        if not self.is_initialized:
            self.initialize()
        
        # Simple rule-based clause extraction for now
        # In production, you'd use the LLM for more sophisticated extraction
        
        sentences = text.split('.')
        clauses = []
        
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            clause_type = "general"
            if any(word in sentence.lower() for word in ["cover", "benefit", "eligible"]):
                clause_type = "coverage"
            elif any(word in sentence.lower() for word in ["exclude", "not cover", "exception"]):
                clause_type = "exclusion"
            elif any(word in sentence.lower() for word in ["condition", "require", "must", "shall"]):
                clause_type = "condition"
            
            clauses.append({
                "clause_id": f"clause_{i}",
                "text": sentence,
                "type": clause_type,
                "importance": 0.5  # Would be determined by LLM in production
            })
        
        return clauses


# Global instance
llm_service = LLMService()
