import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyAxa9KJlmH_OTLSKcqBYEblPlwiPqWcKq0'

import warnings
warnings.filterwarnings('ignore')

from llm.gemini_client import generate_response
from rag.retriever import retrieve_context

query = "What is a deductible?"
context = retrieve_context(query)

print("Testing Gemini API with actual error details:")
print("=" * 70)

try:
    import google.generativeai as genai
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content("Say hello")
    print("✅ Basic test successful!")
    print(f"Response: {response.text}\n")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}")
    print(f"Message: {str(e)}\n")

print("Testing with context:")
print("=" * 70)
try:
    prompt = f"""Context from knowledge base:
{context}

---

User Question: {query}

Based ONLY on the context above, explain the answer in very simple English."""

    import google.generativeai as genai
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    
    SYSTEM_PROMPT = """You are an Insurance Process Explainer."""
    
    model = genai.GenerativeModel(
        model_name='gemini-2.0-flash',
        system_instruction=SYSTEM_PROMPT
    )
    response = model.generate_content(prompt)
    print("✅ Response with context successful!")
    print(f"Response: {response.text}\n")
except Exception as e:
    print(f"❌ Error: {type(e).__name__}")
    print(f"Message: {str(e)}\n")
