"""
Semantic Search Engine - Uses sentence transformers for intelligent document search
Finds relevant text chunks even when query uses different words than document
"""

from sentence_transformers import SentenceTransformer, util
import numpy as np
from typing import List, Dict, Tuple
import torch


class SemanticSearchEngine:
    """
    Semantic search using sentence embeddings
    Understands context and meaning, not just keyword matching
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the search engine
        
        Args:
            model_name: HuggingFace model to use (default is lightweight and fast)
        """
        print(f"Loading semantic search model: {model_name}...")
        self.model = SentenceTransformer(model_name)
        self.chunks = []
        self.embeddings = None
        print("Model loaded successfully!")
    
    def index_documents(self, chunks: List[Dict]) -> None:
        """
        Create embeddings for all document chunks
        
        Args:
            chunks: List of chunk dicts from PDFProcessor.chunk_text()
        """
        print(f"Indexing {len(chunks)} document chunks...")
        
        self.chunks = chunks
        
        # Extract text from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        # Generate embeddings (this is the "AI magic")
        self.embeddings = self.model.encode(
            texts,
            convert_to_tensor=True,
            show_progress_bar=True
        )
        
        print(f"Indexing complete! {len(chunks)} chunks ready for search.")
    
    def search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Search for relevant chunks using semantic similarity
        
        Args:
            query: Search query (e.g., "murder weapon", "surveillance footage")
            top_k: Number of results to return
        
        Returns:
            List of dicts with chunk data + similarity score
        """
        if self.embeddings is None:
            raise ValueError("No documents indexed! Call index_documents() first.")
        
        # Encode the search query
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        # Calculate cosine similarity between query and all chunks
        cos_scores = util.cos_sim(query_embedding, self.embeddings)[0]
        
        # Get top-k most similar chunks
        top_results = torch.topk(cos_scores, k=min(top_k, len(self.chunks)))
        
        results = []
        for score, idx in zip(top_results.values, top_results.indices):
            chunk = self.chunks[idx.item()].copy()
            chunk["similarity_score"] = float(score)
            chunk["score_percentage"] = float(score * 100)
            results.append(chunk)
        
        return results
    
    def search_with_context(self, query: str, top_k: int = 10, context_window: int = 1) -> List[Dict]:
        """
        Search and include surrounding chunks for context
        
        Args:
            query: Search query
            top_k: Number of results
            context_window: Number of chunks before/after to include (default 1)
        
        Returns:
            List of result dicts with 'context_before' and 'context_after' fields
        """
        results = self.search(query, top_k)
        
        # Add context from neighboring chunks
        for result in results:
            chunk_id = result["chunk_id"]
            
            # Find chunks before and after
            context_before = []
            context_after = []
            
            for i in range(1, context_window + 1):
                # Chunk before
                if chunk_id - i >= 0:
                    context_before.insert(0, self.chunks[chunk_id - i]["text"])
                
                # Chunk after
                if chunk_id + i < len(self.chunks):
                    context_after.append(self.chunks[chunk_id + i]["text"])
            
            result["context_before"] = " ".join(context_before) if context_before else None
            result["context_after"] = " ".join(context_after) if context_after else None
        
        return results
    
    def get_stats(self) -> Dict:
        """Get statistics about indexed documents"""
        if not self.chunks:
            return {"status": "No documents indexed"}
        
        total_chars = sum(len(chunk["text"]) for chunk in self.chunks)
        pages = set(chunk["page_num"] for chunk in self.chunks)
        
        return {
            "total_chunks": len(self.chunks),
            "total_pages": len(pages),
            "total_characters": total_chars,
            "avg_chunk_size": total_chars // len(self.chunks),
            "model": self.model._model_config["model_name"] if hasattr(self.model, "_model_config") else "unknown"
        }


# Utility function for testing
def demo_search(chunks: List[Dict], query: str, top_k: int = 5):
    """Quick demo of semantic search"""
    engine = SemanticSearchEngine()
    engine.index_documents(chunks)
    
    print(f"\n{'='*60}")
    print(f"Searching for: '{query}'")
    print(f"{'='*60}\n")
    
    results = engine.search(query, top_k)
    
    for i, result in enumerate(results, 1):
        print(f"Result #{i} (Score: {result['score_percentage']:.1f}%)")
        print(f"Page {result['page_num']}, Chunk {result['chunk_id']}")
        print(f"Text: {result['text'][:200]}...")
        print("-" * 60)
    
    return results


if __name__ == "__main__":
    # Test the search engine
    print("Semantic Search Engine - Test Mode")
    print("This requires running ocr_processor.py first to get chunks")
    print("\nExample usage:")
    print("  from ocr_processor import process_pdf")
    print("  from search_engine import SemanticSearchEngine")
    print("  ")
    print("  _, chunks = process_pdf('document.pdf')")
    print("  engine = SemanticSearchEngine()")
    print("  engine.index_documents(chunks)")
    print("  results = engine.search('murder weapon')")