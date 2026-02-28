"""
Build vector database from knowledge base documents.
Loads .txt files, chunks them, generates embeddings, and stores in ChromaDB.
"""

import os
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


def load_documents(kb_folder):
    """Load all .txt files from knowledge base folder."""
    documents = []
    kb_path = Path(kb_folder)
    
    for txt_file in kb_path.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            documents.append(content)
    
    return documents


def chunk_documents(documents):
    """Split documents into chunks using double newline separator."""
    chunks = []
    
    for doc in documents:
        # Split by double newline
        doc_chunks = doc.split("\n\n")
        
        # Remove empty chunks and strip whitespace
        doc_chunks = [chunk.strip() for chunk in doc_chunks if chunk.strip()]
        chunks.extend(doc_chunks)
    
    return chunks


def build_vector_database():
    """Main function to build the vector database."""
    
    # Initialize embedding model
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load documents from knowledge base
    print("Loading documents from knowledge_base folder...")
    kb_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
    documents = load_documents(kb_folder)
    print(f"Loaded {len(documents)} documents")
    
    # Chunk documents
    print("Chunking documents...")
    chunks = chunk_documents(documents)
    print(f"Created {len(chunks)} chunks")
    
    if not chunks:
        print("No chunks found. Please add .txt files to knowledge_base folder.")
        return
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(chunks, show_progress_bar=True)
    
    # Initialize ChromaDB client
    print("Initializing ChromaDB...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Delete existing collection if it exists
    try:
        client.delete_collection("insurance_kb")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(name="insurance_kb")
    
    # Generate unique IDs for chunks
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    
    # Add documents to collection
    print("Storing embeddings in ChromaDB...")
    collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        ids=ids
    )
    
    print(f"\n✓ Success! Vector database built with {len(chunks)} chunks.")
    print(f"Database location: {db_path}")


if __name__ == "__main__":
    build_vector_database()
