"""
Build vector database from knowledge base documents.
Optimized for multilingual, step-by-step content with proper chunking.
"""

import os
import re
from pathlib import Path
from sentence_transformers import SentenceTransformer
import chromadb


def clean_text(text):
    """Clean and normalize text while preserving structure."""
    # Remove excessive whitespace but keep paragraph breaks
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def load_documents(kb_folder):
    """Load all .txt files with metadata."""
    documents = []
    metadata = []
    kb_path = Path(kb_folder)
    
    for txt_file in sorted(kb_path.glob("*.txt")):
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
            documents.append(content)
            metadata.append({"source": txt_file.name})
    
    return documents, metadata


def detect_content_type(text):
    """Detect if chunk is flowchart, language section, or regular."""
    if 'FLOWCHART_FORMAT' in text:
        return 'flowchart'
    elif any(lang in text for lang in ['English:', 'Hindi:', 'Telugu:']):
        return 'multilingual'
    return 'regular'


def smart_chunk_documents(documents, metadata, max_words=200, min_words=30):
    """
    Smart chunking that preserves:
    - Language sections (English, Hindi, Telugu)
    - Flowchart format
    - Step-by-step structure
    """
    chunks = []
    chunk_metadata = []
    
    for doc_idx, doc in enumerate(documents):
        # Split by section headers first (---)
        sections = doc.split('\n---\n')
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
            
            # Check if section contains language-specific content
            if 'English:' in section:
                # This is a multilingual section, keep it together
                chunks.append(section)
                chunk_metadata.append({
                    "source": metadata[doc_idx]["source"],
                    "type": "multilingual",
                    "has_english": 'English:' in section,
                    "has_hindi": 'Hindi:' in section,
                    "has_telugu": 'Telugu:' in section
                })
                continue
            
            if 'FLOWCHART_FORMAT' in section:
                # Keep flowchart sections intact
                chunks.append(section)
                chunk_metadata.append({
                    "source": metadata[doc_idx]["source"],
                    "type": "flowchart"
                })
                continue
            
            # For regular sections, check if it's step-by-step
            if 'Step' in section and '->' in section:
                # Preserve steps structure
                chunks.append(section)
                chunk_metadata.append({
                    "source": metadata[doc_idx]["source"],
                    "type": "steps"
                })
                continue
            
            # For other regular content, chunk by size
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                para = para.strip()
                if not para or len(para.split()) < 5:
                    continue
                
                # Check if adding this paragraph exceeds max size
                test_chunk = (current_chunk + "\n\n" + para).strip() if current_chunk else para
                word_count = len(test_chunk.split())
                
                if word_count > max_words and current_chunk:
                    # Save current chunk
                    if len(current_chunk.split()) >= min_words:
                        chunks.append(current_chunk)
                        chunk_metadata.append({
                            "source": metadata[doc_idx]["source"],
                            "type": "regular"
                        })
                    current_chunk = para
                else:
                    current_chunk = test_chunk
            
            # Add remaining chunk
            if current_chunk and len(current_chunk.split()) >= min_words:
                chunks.append(current_chunk)
                chunk_metadata.append({
                    "source": metadata[doc_idx]["source"],
                    "type": "regular"
                })
    
    return chunks, chunk_metadata


def remove_empty_chunks(chunks, chunk_metadata):
    """Remove empty or very short chunks."""
    valid_chunks = []
    valid_metadata = []
    
    for chunk, meta in zip(chunks, chunk_metadata):
        if chunk.strip() and len(chunk.split()) >= 10:
            valid_chunks.append(chunk)
            valid_metadata.append(meta)
    
    return valid_chunks, valid_metadata


def build_vector_database():
    """Main function to build optimized vector database."""
    
    # Initialize embedding model (loaded once globally)
    print("Loading embedding model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # Load documents from knowledge base
    print("Loading documents from knowledge_base folder...")
    kb_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
    documents, metadata = load_documents(kb_folder)
    print(f"✓ Loaded {len(documents)} documents")
    
    if not documents:
        print("✗ No documents found. Please add .txt files to knowledge_base folder.")
        return
    
    # Smart chunking preserving multilingual and step structure
    print("Creating semantic chunks...")
    chunks, chunk_metadata = smart_chunk_documents(documents, metadata, max_words=200, min_words=30)
    print(f"✓ Created {len(chunks)} chunks")
    
    # Remove empty chunks
    print("Validating chunks...")
    chunks, chunk_metadata = remove_empty_chunks(chunks, chunk_metadata)
    print(f"✓ Validated {len(chunks)} chunks")
    
    if not chunks:
        print("✗ No valid chunks created.")
        return
    
    # Generate embeddings with batch processing
    print("Generating embeddings...")
    embeddings = model.encode(chunks, show_progress_bar=True, batch_size=32)
    
    # Initialize ChromaDB client
    print("Initializing ChromaDB...")
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
    client = chromadb.PersistentClient(path=db_path)
    
    # Delete existing collection to prevent duplicates
    try:
        client.delete_collection("insurance_kb")
        print("✓ Cleaned existing collection")
    except:
        pass
    
    # Create new collection
    collection = client.create_collection(name="insurance_kb")
    
    # Generate unique IDs based on source and type
    ids = [f"{meta['source']}_{meta.get('type', 'regular')}_{i}" 
           for i, meta in enumerate(chunk_metadata)]
    
    # Prepare metadata for storage
    metadatas = [
        {
            "source": meta["source"],
            "type": meta.get("type", "regular"),
            "has_english": str(meta.get("has_english", False)),
            "has_hindi": str(meta.get("has_hindi", False)),
            "has_telugu": str(meta.get("has_telugu", False))
        } 
        for meta in chunk_metadata
    ]
    
    # Add documents to collection
    print("Storing embeddings in ChromaDB...")
    collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        ids=ids,
        metadatas=metadatas
    )
    
    # Print success summary
    print(f"\n✓ Vector database built successfully!")
    print(f"  - Total chunks: {len(chunks)}")
    print(f"  - Database location: {db_path}")
    print(f"  - Min chunk words: {min([len(c.split()) for c in chunks])}")
    print(f"  - Max chunk words: {max([len(c.split()) for c in chunks])}")
    print(f"  - Collection: insurance_kb")


if __name__ == "__main__":
    build_vector_database()
