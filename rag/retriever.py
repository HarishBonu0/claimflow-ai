"""
RAG retriever module for querying the vector database.
Optimized for retrieval quality, performance, and relevance filtering.
"""

import os
import re
from sentence_transformers import SentenceTransformer
import chromadb


# Initialize model and database connection globally (loaded once)
model = SentenceTransformer('all-MiniLM-L6-v2')

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection(name="insurance_kb")


def clean_query(query):
    """Clean and normalize query text."""
    # Remove excessive whitespace
    query = re.sub(r'\s+', ' ', query)
    return query.strip()


def retrieve_context(query, k=3, min_similarity=0.3):
    """
    Retrieve relevant context from vector database with quality filtering.
    
    Args:
        query: Search query string
        k: Number of top matching chunks to retrieve (default: 3)
        min_similarity: Minimum similarity score threshold (default: 0.3)
    
    Returns:
        String containing retrieved context joined with double newlines
    """
    
    try:
        # Clean query
        query = clean_query(query)
        
        if not query:
            return ""
        
        # Convert query to embedding
        query_embedding = model.encode(query).tolist()
        
        # Query the collection with more results than needed for filtering
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k * 2, 10)  # Get extra results for filtering
        )
        
        # Extract documents and distances
        documents = results.get('documents', [[]])
        distances = results.get('distances', [[]])
        
        # Handle empty results
        if not documents or not documents[0]:
            return ""
        
        # Filter by similarity score (distance: lower is better)
        # Convert distance to similarity: similarity = 1 - (distance / 2) for cosine
        filtered_docs = []
        for doc, dist in zip(documents[0], distances[0]):
            similarity = 1 - (dist / 2)  # Approximate similarity from distance
            if similarity >= min_similarity and doc.strip():
                filtered_docs.append(doc)
        
        # Take top k after filtering
        filtered_docs = filtered_docs[:k]
        
        # Return empty if no results passed the filter
        if not filtered_docs:
            return ""
        
        # Remove duplicate chunks from results
        unique_docs = []
        seen = set()
        for doc in filtered_docs:
            normalized = doc.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_docs.append(doc)
        
        # Join retrieved chunks
        context = "\n\n".join(unique_docs)
        
        return context
    
    except Exception as e:
        # Safe error handling - never crash
        print(f"Warning: Retrieval error - {str(e)}")
        return ""


if __name__ == "__main__":
    # Test example
    print("Testing retriever with sample query...\n")
    print("Query: 'explain claim assessment stage'\n")
    print("-" * 60)
    
    result = retrieve_context("explain claim assessment stage")
    if result:
        print(result)
    else:
        print("No relevant context found.")

