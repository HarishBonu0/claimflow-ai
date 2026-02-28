"""
RAG retriever module for querying the vector database.
Converts queries to embeddings and retrieves relevant context.
"""

import os
from sentence_transformers import SentenceTransformer
import chromadb


# Initialize model and database connection
model = SentenceTransformer('all-MiniLM-L6-v2')

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection(name="insurance_kb")


def retrieve_context(query, k=3):
    """
    Retrieve relevant context from vector database.
    
    Args:
        query: Search query string
        k: Number of top matching chunks to retrieve (default: 3)
    
    Returns:
        String containing retrieved context joined with double newlines
    """
    
    # Convert query to embedding
    query_embedding = model.encode(query).tolist()
    
    # Query the collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k
    )
    
    # Extract documents from results
    documents = results.get('documents', [[]])
    
    # Handle empty results
    if not documents or not documents[0]:
        return "No relevant context found."
    
    # Join retrieved chunks
    context = "\n\n".join(documents[0])
    
    return context


if __name__ == "__main__":
    # Test example
    print("Testing retriever with sample query...\n")
    print("Query: 'why insurance claims take time'\n")
    print("-" * 60)
    
    result = retrieve_context("why insurance claims take time")
    print(result)
