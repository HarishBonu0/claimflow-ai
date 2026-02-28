"""
RAG retriever module for querying the vector database.
Optimized for simple English, multilingual content, and step-by-step retrieval.
"""

import os
import re
from sentence_transformers import SentenceTransformer
import chromadb


# Initialize model and database globally (only once)
model = SentenceTransformer('all-MiniLM-L6-v2')

db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_db")
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection(name="insurance_kb")


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
            return ""
        
        # Convert query to embedding
        query_embedding = model.encode(query).tolist()
        
        # Query the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(k * 3, 15)  # Get extra for filtering
        )
        
        # Extract documents and metadata
        documents = results.get('documents', [[]])
        metadatas = results.get('metadatas', [[]])
        distances = results.get('distances', [[]])
        
        if not documents or not documents[0]:
            return ""
        
        # Filter and rank results
        ranked_results = []
        
        for doc, meta, dist in zip(documents[0], metadatas[0], distances[0]):
            if not doc.strip():
                continue
            
            # Calculate relevance score
            similarity = 1 - (dist / 2)
            
            # Skip low relevance
            if similarity < min_similarity:
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
            return ""
        
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
        
        return context
    
    except Exception as e:
        # Safe error handling
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

