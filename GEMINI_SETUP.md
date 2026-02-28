# Gemini Flash Integration Setup Guide

## Overview
This document explains how to set up and use the Gemini Flash integration with the RAG system.

## What is Included

- `llm/gemini_client.py` - Gemini Flash API integration
- `llm/integration_example.py` - Complete RAG + Gemini example
- Function: `retrieve_context(query)` - RAG retrieval (from rag/retriever.py)
- Function: `generate_response(query, context)` - Gemini generation

## Step 1: Get a Gemini API Key

1. Visit: https://aistudio.google.com/apikey
2. Click "Create API key"
3. Copy your API key (keep it secret!)

## Step 2: Set Environment Variable

### On Windows (Command Prompt):
```bash
setx GEMINI_API_KEY "your_api_key_here"
```
Then restart your terminal/IDE.

### On Windows (PowerShell):
```powershell
$env:GEMINI_API_KEY = "your_api_key_here"
```

### On Linux/Mac:
```bash
export GEMINI_API_KEY="your_api_key_here"
```

Add to `~/.bashrc` for persistence.

## Step 3: Usage Examples

### Basic Usage:
```python
from rag.retriever import retrieve_context
from llm.gemini_client import generate_response

# Step 1: Retrieve context
context = retrieve_context("What is a deductible?")

# Step 2: Generate answer
answer = generate_response("What is a deductible?", context)

print(answer)
```

### Complete Pipeline:
```python
from llm.integration_example import answer_query

# One-line usage
answer = answer_query("Explain the claim process")
print(answer)

# With debug info
answer = answer_query("What is fraud?", verbose=True)
```

### With Custom Parameters:
```python
from llm.gemini_client import generate_response
from rag.retriever import retrieve_context

context = retrieve_context("Your question here", k=5)

# Custom temperature and token limit
answer = generate_response(
    "Your question here",
    context,
    temperature=0.5,  # More creative (0.0-1.0)
    max_tokens=800    # Longer response
)

print(answer)
```

## System Architecture

```
User Query
    ↓
[RAG System]  ← retrieve_context()
    ↓
Context Retrieval
    ↓
[Gemini Flash] ← generate_response()
    ↓
User-Friendly Answer
```

## Key Features

✅ Simple English output
✅ Beginner-friendly explanations
✅ Step-by-step breakdowns
✅ Safe error handling
✅ No claim approval/rejection
✅ Educational financial content only
✅ Temperature: 0.4 (consistent, factual)
✅ Max tokens: 600 (concise answers)

## Parameters

### `retrieve_context(query, k=3, min_similarity=0.25, lang='en')`
- `query`: User's question
- `k`: Number of context chunks (default: 3)
- `min_similarity`: Relevance threshold (default: 0.25)
- `lang`: Language 'en'=English, 'all'=all languages

### `generate_response(query, context, temperature=0.4, max_tokens=600)`
- `query`: User's question
- `context`: Retrieved context from RAG
- `temperature`: Model creativity (0.0-1.0, lower=factual)
- `max_tokens`: Response length limit

## Troubleshooting

### "GEMINI_API_KEY not set"
- Environment variable not configured
- Solution: Follow "Step 2" above

### "API Key Invalid"
- Key is incorrect or expired
- Solution: Get a new key from aistudio.google.com/apikey

### "Rate Limit Exceeded"
- Too many requests too quickly
- Solution: Wait a moment and try again

### "No Context Found"
- RAG didn't find relevant information
- Message: "I could not find enough information. Please ask in another way."

## Testing

### Test RAG Only:
```bash
python rag/retriever.py
```

### Test Gemini Integration:
```bash
python llm/gemini_client.py
```

### Test Complete Pipeline:
```bash
python llm/integration_example.py
```

## Important Notes

⚠️ **NEVER**:
- Hard-code API keys in code
- Commit API keys to git
- Share your API key publicly
- Use the API key in client-facing code

✅ **ALWAYS**:
- Use environment variables for API keys
- Keep API keys secret and secure
- Add `.env` to `.gitignore`
- Review the system prompt before deployment

## System Prompt Details

The system prompt defines Gemini's behavior:

```
- Explain in VERY simple English
- Use short sentences
- Be beginner-friendly
- Explain steps one by one
- NEVER approve/reject claims
- NEVER interpret policy coverage
- Financial content is educational only
- Always be helpful and supportive
```

## Model Information

- **Model**: gemini-1.5-flash
- **Provider**: Google Gemini
- **Cost**: Very affordable (free tier available)
- **Speed**: Fast responses
- **Context Window**: Large (can handle detailed context)

## Integration with Streamlit (Future)

When ready to add UI:
```python
import streamlit as st
from llm.integration_example import answer_query

st.title("Insurance Claims Explainer")
question = st.text_input("Ask a question:")
if question:
    answer = answer_query(question, verbose=False)
    st.write(answer)
```

## Next Steps

1. Set GEMINI_API_KEY environment variable
2. Run: `python llm/gemini_client.py`
3. Run: `python llm/integration_example.py`
4. Integrate into your application

---

**Version**: 1.0
**Last Updated**: February 28, 2026
**Status**: Production Ready
