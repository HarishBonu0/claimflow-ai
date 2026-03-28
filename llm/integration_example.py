"""
Complete RAG + Gemini Integration Example
Shows how to use the RAG system with Gemini Flash for answers.
"""

import logging
import sys
import os

# Add project root to Python path for proper module imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from llm.gemini_client import generate_response, generate_response_with_history

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


def _is_rag_enabled() -> bool:
    """Allow disabling heavy vector retrieval on low-memory deployments."""
    return os.getenv("ENABLE_RAG", "true").strip().lower() in {"1", "true", "yes", "on"}


def answer_query(user_query, context_k=3, verbose=False, conversation_history=None):
    """
    Complete pipeline: RAG retrieval + Gemini generation with conversation context.
    
    Args:
        user_query: User's question
        context_k: Number of chunks to retrieve (default: 3)
        verbose: Print debug info (default: False)
        conversation_history: List of previous messages for context (default: None)
    
    Returns:
        User-friendly answer
    """
    
    try:
        if verbose:
            print(f"📋 Question: {user_query}")
            logger.info(f"Processing query: {user_query[:100]}...")
        
        # Step 1: Retrieve context using RAG when enabled.
        context = ""
        if _is_rag_enabled():
            try:
                from rag.retriever import retrieve_context
                context = retrieve_context(user_query, k=context_k)

                if verbose:
                    if context:
                        print(f"📚 Context found: {len(context)} characters")
                        logger.debug(f"Retrieved context: {context[:200]}...")
                    else:
                        print("⚠️ No context found")
                        logger.warning("No context retrieved for query")
            except Exception as e:
                logger.error(f"Error retrieving context: {type(e).__name__}: {e}", exc_info=True)
                context = ""
                if verbose:
                    print(f"⚠️ Context retrieval failed: {e}")
        else:
            logger.info("RAG retrieval disabled (ENABLE_RAG=false). Using Gemini response without vector context.")
        
        # Step 2: Generate answer using Gemini with conversation history
        try:
            if conversation_history:
                answer = generate_response_with_history(user_query, context, conversation_history)
            else:
                answer = generate_response(user_query, context)
            
            if verbose:
                print(f"🤖 Generated answer")
                logger.info("Answer generated successfully")
            
            return answer
        except Exception as e:
            logger.error(f"Error generating response: {type(e).__name__}: {e}", exc_info=True)
            if verbose:
                print(f"⚠️ Error generating response: {e}")
            return f"Failed to generate response: {str(e)}"
    
    except Exception as e:
        logger.error(f"Unexpected error in answer_query: {type(e).__name__}: {e}", exc_info=True)
        return f"An unexpected error occurred: {str(e)}"


if __name__ == "__main__":
    """
    Test the complete integration.
    """
    
    print("=" * 70)
    print("RAG + Gemini Flash Integration Test")
    print("=" * 70)
    
    # Test queries
    questions = [
        "What is a deductible?",
        "How long does an insurance claim take?",
        "What should I do if my claim is rejected?",
        "Explain the claim process",
        "What is fraud and why is it bad?",
    ]
    
    for q in questions:
        print(f"\n{'='*70}")
        answer = answer_query(q, verbose=True)
        print(f"\n[OK] Answer:\n{answer}")
    
    print(f"\n{'='*70}")
    print("Integration test completed!")
    print("=" * 70)
