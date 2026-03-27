"""
RAG retriever module for querying the vector database.
Optimized for simple English, multilingual content, and step-by-step retrieval.
"""

import os
import re
import logging
import sys
from pathlib import Path

# Set environment variables BEFORE importing sentence-transformers
os.environ['HF_HUB_DISABLE_IMPLICIT_TOKEN'] = '1'
os.environ['HF_HUB_OFFLINE'] = '0'

from sentence_transformers import SentenceTransformer
import chromadb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Initialize model and database globally (only once)
try:
    logger.info("Loading SentenceTransformer model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2', trust_remote_code=False, device='cpu')
    logger.info("[OK] SentenceTransformer model loaded successfully")
except Exception as e:
    logger.warning(f"Retrying SentenceTransformer model load from offline cache: {type(e).__name__}")
    try:
        # Try loading offline from cache
        os.environ['HF_HUB_OFFLINE'] = '1'
        model = SentenceTransformer('all-MiniLM-L6-v2', trust_remote_code=False, device='cpu')
        logger.info("[OK] SentenceTransformer model loaded from offline cache")
    except Exception as e2:
        logger.error(f"[ERROR] Failed to load SentenceTransformer model: {type(e2).__name__}: {e2}", exc_info=True)
        raise

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
logger.info(f"Using vector database path: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    logger.info("[OK] ChromaDB client initialized successfully")
except Exception as e:
    logger.error(f"[ERROR] Failed to initialize ChromaDB client: {type(e).__name__}: {e}", exc_info=True)
    raise

def get_or_create_collection():
    """Get existing collection or create a new one with default content."""
    try:
        collection = client.get_collection(name="insurance_kb")
        logger.info("[OK] Loaded existing insurance_kb collection")
        return collection
    except Exception as e:
        logger.warning(f"Collection not found: {e}. Creating new collection...")
        try:
            # Collection doesn't exist, create it with default content
            collection = client.create_collection(name="insurance_kb", metadata={"hnsw:space": "cosine"})
            logger.info("[OK] Created new insurance_kb collection")
            
            # Load and add default knowledge base documents
            load_default_documents(collection)
            return collection
        except Exception as create_error:
            logger.error(f"[ERROR] Failed to create collection: {type(create_error).__name__}: {create_error}", exc_info=True)
            raise

def load_default_documents(collection):
    """Load default insurance documents into the collection."""
    kb_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "knowledge_base")
    kb_path = Path(kb_folder)
    
    logger.info(f"Loading knowledge base from: {kb_folder}")
    
    if not kb_path.exists():
        logger.error(f"[ERROR] Knowledge base folder not found: {kb_folder}")
        return
    
    doc_count = 0
    error_count = 0
    
    for txt_file in sorted(kb_path.glob("*.txt")):
        try:
            with open(txt_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    # Split content into chunks
                    chunks = [chunk.strip() for chunk in content.split('\n---\n') if chunk.strip()]
                    
                    for idx, chunk in enumerate(chunks):
                        if chunk:
                            try:
                                # Create document ID and embedding
                                doc_id = f"{txt_file.stem}_{idx}"
                                embedding = model.encode(chunk, convert_to_tensor=False)
                                
                                # Add to collection
                                collection.add(
                                    ids=[doc_id],
                                    embeddings=[embedding.tolist()],
                                    documents=[chunk],
                                    metadatas=[{"source": txt_file.name, "chunk": idx}]
                                )
                                doc_count += 1
                            except Exception as chunk_error:
                                logger.error(f"[ERROR] Error processing chunk {doc_id}: {type(chunk_error).__name__}: {chunk_error}")
                                error_count += 1
        except Exception as e:
            logger.error(f"[ERROR] Error loading {txt_file.name}: {type(e).__name__}: {e}")
            error_count += 1
    
    if doc_count > 0:
        logger.info(f"[OK] Loaded {doc_count} document chunks into vector database")
    if error_count > 0:
        logger.warning(f"[WARNING] Encountered {error_count} errors while loading documents")

collection = get_or_create_collection()


def clean_query(query):
    """Clean and normalize query."""
    query = re.sub(r'\s+', ' ', query)
    return query.strip()


def extract_english_section(text):
    """Extract only English section from multilingual content."""
    if 'English:' in text:
        # Find English section
        parts = text.split('\n')
        english_content = []
        in_english = False
        
        for line in parts:
            if 'English:' in line:
                in_english = True
                continue
            elif any(lang in line for lang in ['Hindi:', 'Telugu:', 'FLOWCHART']):
                in_english = False
            elif in_english and line.strip():
                english_content.append(line.strip())
        
        if english_content:
            return '\n'.join(english_content).strip()
    
    return text.strip()


def make_speech_friendly(text):
    """
    Clean text for speech.
    Remove extra formatting, make short friendly sentences.
    """
    # Remove markdown and special formatting
    text = re.sub(r'\*+', '', text)
    text = re.sub(r'#+', '', text)
    text = re.sub(r'_+', '', text)
    
    # Replace arrows with readable text
    text = text.replace('->', ' leads to ')
    text = text.replace('<-', ' comes from ')
    
    # Clean extra spaces
    text = re.sub(r'\s{2,}', ' ', text)
    
    return text.strip()


def retrieve_context(query, k=3, min_similarity=0.25, lang='en'):
    """
    Retrieve relevant context from vector database.
    Optimized for simple English, multilingual content, and speech.
    
    Args:
        query: Search query string
        k: Number of matches to retrieve (default: 3)
        min_similarity: Minimum relevance score (default: 0.25)
        lang: Language preference 'en'=English only, 'all'=all languages
    
    Returns:
        Clean, speech-friendly text joined with spaces.
    """
    
    try:
        # Clean query
        query = clean_query(query)
        
        if not query or len(query.split()) < 2:
            logger.warning(f"Query too short or empty: {query}")
            return ""
        
        logger.debug(f"Retrieving context for query: {query}")
        
        # Convert query to embedding
        try:
            query_embedding = model.encode(query).tolist()
        except Exception as e:
            logger.error(f"❌ Error encoding query: {type(e).__name__}: {e}", exc_info=True)
            return ""
        
        # Query the collection
        try:
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(k * 3, 15)  # Get extra for filtering
            )
        except Exception as e:
            logger.error(f"❌ Error querying collection: {type(e).__name__}: {e}", exc_info=True)
            return ""
        
        # Extract documents and metadata
        documents = results.get('documents', [[]])
        metadatas = results.get('metadatas', [[]])
        distances = results.get('distances', [[]])
        
        if not documents or not documents[0]:
            logger.debug("No documents found in query results")
            return ""
        
        logger.debug(f"Retrieved {len(documents[0])} candidate documents, filtering...")
        
        # Filter and rank results
        ranked_results = []
        
        for doc, meta, dist in zip(documents[0], metadatas[0], distances[0]):
            if not doc.strip():
                continue
            
            # Calculate relevance score
            similarity = 1 - (dist / 2)
            
            # Skip low relevance
            if similarity < min_similarity:
                logger.debug(f"Skipping low relevance doc: similarity={similarity:.2f}")
                continue
            
            # Extract English if multilingual
            if lang == 'en' and meta.get('type') == 'multilingual':
                doc = extract_english_section(doc)
            
            # Skip if empty after extraction
            if not doc.strip():
                continue
            
            ranked_results.append({
                'doc': doc,
                'type': meta.get('type', 'regular'),
                'similarity': similarity
            })
        
        # Sort by similarity
        ranked_results = sorted(ranked_results, key=lambda x: x['similarity'], reverse=True)
        
        # Take top k
        ranked_results = ranked_results[:k]
        
        if not ranked_results:
            logger.warning(f"No relevant documents found for query (threshold: {min_similarity})")
            return ""
        
        logger.info(f"✓ Found {len(ranked_results)} relevant documents")
        
        # Remove duplicates
        unique_docs = []
        seen = set()
        
        for result in ranked_results:
            doc = result['doc']
            normalized = doc.lower().strip()[:100]  # Check first 100 chars
            
            if normalized not in seen:
                seen.add(normalized)
                unique_docs.append(doc)
        
        # Make speech-friendly
        final_output = []
        for doc in unique_docs:
            doc = make_speech_friendly(doc)
            if doc:
                final_output.append(doc)
        
        # Join with spaces for natural speech flow
        context = " ".join(final_output)
        
        logger.debug(f"Context prepared: {len(context)} characters")
        return context
    
    except Exception as e:
        # Safe error handling
        logger.error(f"❌ Unexpected error in retrieve_context: {type(e).__name__}: {e}", exc_info=True)
        return ""


if __name__ == "__main__":
    # Test with sample queries
    print("=" * 60)
    print ("Testing RAG Retriever")
    print("=" * 60)
    
    test_queries = [
        "explain claim assessment stage",
        "what is deductible",
        "insurance claim process",
        "how long does claim take"
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        print("-" * 60)
        result = retrieve_context(query, k=2)
        if result:
            print(result)
        else:
            print("No relevant context found.")
        print()

