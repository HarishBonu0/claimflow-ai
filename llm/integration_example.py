"""
Complete RAG + Gemini Integration Example
Shows how to use the RAG system with Gemini Flash for answers.
"""

from rag.retriever import retrieve_context
from llm.gemini_client import generate_response


def answer_query(user_query, context_k=3, verbose=False):
    """
    Complete pipeline: RAG retrieval + Gemini generation.
    
    Args:
        user_query: User's question
        context_k: Number of chunks to retrieve (default: 3)
        verbose: Print debug info (default: False)
    
    Returns:
        User-friendly answer
    """
    
    if verbose:
        print(f"📋 Question: {user_query}")
    
    # Step 1: Retrieve context using RAG
    context = retrieve_context(user_query, k=context_k)
    
    if verbose:
        if context:
            print(f"📚 Context found: {len(context)} characters")
        else:
            print("⚠️ No context found")
    
    # Step 2: Generate answer using Gemini
    answer = generate_response(user_query, context)
    
    if verbose:
        print(f"🤖 Generated answer")
    
    return answer


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
        print(f"\n✅ Answer:\n{answer}")
    
    print(f"\n{'='*70}")
    print("Integration test completed!")
    print("=" * 70)
