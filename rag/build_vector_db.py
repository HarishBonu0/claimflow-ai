"""
Build vector database from knowledge base documents.
Optimized for performance, semantic chunking, and retrieval quality.
"""

import os
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


def clean_text(text):
    """Clean and normalize text."""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?;:()\-]', '', text)
    return text.strip()


def load_documents(kb_folder):
    """Load all .txt files with metadata."""
    documents = []
    metadata = []
    kb_path = Path(kb_folder)
    
    for txt_file in kb_path.glob("*.txt"):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            documents.append(content)
            metadata.append({"source": txt_file.name})
    
    return documents, metadata


def smart_chunk_documents(documents, metadata, max_words=150, min_words=20):
    """
    Split documents into semantic chunks with size control.
    Ensures chunks are meaningful and not too large or small.
    """
    chunks = []
    chunk_metadata = []
    
    for doc_idx, doc in enumerate(documents):
        # Split by double newline first (paragraph-level)
        paragraphs = doc.split("\n\n")
        
        current_chunk = ""
        chunk_index = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # Clean the paragraph
            para = clean_text(para)
            
            # Skip if too short or nonsensical
            if len(para.split()) < 5:
                continue
            
            # If paragraph itself is large enough, save it as a chunk
            para_words = len(para.split())
            if para_words >= min_words and para_words <= max_words:
                chunks.append(para)
                chunk_metadata.append({
                    "source": metadata[doc_idx]["source"],
                    "chunk_index": chunk_index
                })
                chunk_index += 1
                continue
            
            # Check if adding this paragraph exceeds max size
            combined = (current_chunk + "\n\n" + para).strip() if current_chunk else para
            word_count = len(combined.split())
            
            if word_count > max_words and current_chunk:
                # Save current chunk
                if len(current_chunk.split()) >= min_words:
                    chunks.append(current_chunk)
                    chunk_metadata.append({
                        "source": metadata[doc_idx]["source"],
                        "chunk_index": chunk_index
                    })
                    chunk_index += 1
                current_chunk = para
            else:
                current_chunk = combined
        
        # Add remaining chunk if it meets minimum size
        if current_chunk and len(current_chunk.split()) >= min_words:
            chunks.append(current_chunk)
            chunk_metadata.append({
                "source": metadata[doc_idx]["source"],
                "chunk_index": chunk_index
            })
    
    return chunks, chunk_metadata


def remove_duplicate_chunks(chunks, chunk_metadata, similarity_threshold=0.95):
    """Remove near-duplicate chunks to improve quality."""
    if not chunks:
        return chunks, chunk_metadata
    
    unique_chunks = []
    unique_metadata = []
    seen_texts = set()
    
    for chunk, meta in zip(chunks, chunk_metadata):
        # Simple deduplication using normalized text
        normalized = chunk.lower().strip()
        if normalized not in seen_texts:
            seen_texts.add(normalized)
            unique_chunks.append(chunk)
            unique_metadata.append(meta)
    
    return unique_chunks, unique_metadata


def build_vector_database():
    """Main function to build optimized vector database."""
    
    # Initialize embedding model (loaded once)
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load documents from knowledge base
    print("Loading documents from knowledge_base folder...")
    kb_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
    documents, metadata = load_documents(kb_folder)
    print(f"Loaded {len(documents)} documents")
    
    if not documents:
        print("No documents found. Please add .txt files to knowledge_base folder.")
        return
    
    # Smart chunking with size control
    print("Creating semantic chunks...")
    chunks, chunk_metadata = smart_chunk_documents(documents, metadata, max_words=150, min_words=20)
    print(f"Created {len(chunks)} initial chunks")
    
    # Remove duplicates
    print("Removing duplicate chunks...")
    chunks, chunk_metadata = remove_duplicate_chunks(chunks, chunk_metadata)
    print(f"Retained {len(chunks)} unique chunks")
    
    if not chunks:
        print("No valid chunks created. Please check your documents.")
        return
    
    # Generate embeddings
    print("Generating embeddings...")
    embeddings = model.encode(chunks, show_progress_bar=True, batch_size=32)
    
    # Initialize ChromaDB client
    print("Initializing ChromaDB...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Delete existing collection if it exists to prevent duplicates
    try:
        client.delete_collection("insurance_kb")
        print("Deleted existing collection")
    except:
        pass
    
    # Create collection
    collection = client.create_collection(name="insurance_kb")
    
    # Generate unique IDs using source and index
    ids = [f"{meta['source']}_{meta['chunk_index']}" for meta in chunk_metadata]
    
    # Prepare metadata for storage
    metadatas = [{"source": meta["source"], "chunk_index": str(meta["chunk_index"])} for meta in chunk_metadata]
    
    # Add documents to collection with metadata
    print("Storing embeddings in ChromaDB...")
    collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )
    
    print(f"\n✓ Success! Vector database built with {len(chunks)} chunks.")
    print(f"✓ Database location: {db_path}")
    print(f"✓ Chunks range from {min([len(c.split()) for c in chunks])} to {max([len(c.split()) for c in chunks])} words")


if __name__ == "__main__":
    build_vector_database()
