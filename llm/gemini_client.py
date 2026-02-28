"""
Gemini Flash integration for RAG system.
Converts retrieved context into simple, user-friendly answers.
"""

import os
import re
import google.generativeai as genai


# Load API key from environment
API_KEY = os.getenv('GEMINI_API_KEY')

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")

# Configure Gemini
genai.configure(api_key=API_KEY)

# System prompt for insurance explainer
SYSTEM_PROMPT = """You are an Insurance Process Explainer.

Your role:
- Explain insurance concepts in VERY simple English.
- Use short, clear sentences.
- Be beginner-friendly and easy to understand.
- If the context shows steps, explain them one by one.
- Use examples when helpful.

Important Rules:
- NEVER approve or reject insurance claims.
- NEVER interpret specific policy coverage.
- NEVER give legal or financial advice.
- Financial explanations are educational only.
- Always be helpful and supportive.

Style:
- Use simple words (no jargon).
- Keep sentences short (1 topic per sentence).
- Use bullet points for lists.
- Be friendly and encouraging.
- Acknowledge if information is incomplete."""


def generate_response(query, context, temperature=0.4, max_tokens=600):
    """
    Generate user-friendly answer based on retrieved context.
    
    Args:
        query: User's original question
        context: Retrieved context from RAG
        temperature: Model creativity (default: 0.4 - low for consistency)
        max_tokens: Maximum response length (default: 600)
    
    Returns:
        Simple, friendly explanation
    """
    
    # Handle empty context
    if not context or not context.strip():
        return "I could not find enough information. Please ask in another way."
    
    try:
        # Build prompt message
        prompt = f"""Context from knowledge base:
{context}

---

User Question: {query}

Based ONLY on the context above, explain the answer in very simple English. 
Be friendly and use short sentences."""
        
        # Create model instance
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            ),
            system_instruction=SYSTEM_PROMPT
        )
        
        # Generate response
        response = model.generate_content(prompt)
        
        # Extract and clean text
        answer = response.text.strip() if response.text else ""
        
        if not answer:
            return "I could not find enough information. Please ask in another way."
        
        return answer
    
    except Exception as e:
        # Handle API errors gracefully
        error_msg = str(e)
        if "API key" in error_msg:
            return "API configuration error. Please check your API key."
        elif "rate limit" in error_msg.lower():
            return "Service temporarily busy. Please try again in a moment."
        else:
            return f"I encountered an error while processing your question. Please try again."


def simple_answer(query, context):
    """
    Simplified version - just calls generate_response with defaults.
    For quick integration.
    """
    return generate_response(query, context)


if __name__ == "__main__":
    # Test integration
    from rag.retriever import retrieve_context
    
    print("=" * 70)
    print("Gemini Flash + RAG Integration Test")
    print("=" * 70)
    
    test_queries = [
        "Explain claim assessment stage",
        "What is deductible",
        "How long does claim take",
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        print("-" * 70)
        
        # Retrieve context
        context = retrieve_context(query, k=2)
        
        if context:
            print(f"📚 Context retrieved: {len(context)} characters")
        else:
            print("⚠️ No context found")
        
        # Generate response
        answer = generate_response(query, context)
        print(f"\n🤖 Answer:\n{answer}")
        print()
    
    print("=" * 70)
