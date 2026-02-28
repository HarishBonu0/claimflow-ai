"""
Integration Test Script
Tests all components: RAG + LLM + Voice Assistant
"""

import os
import sys

print("=" * 70)
print("INTEGRATION TEST - ClaimFlow AI")
print("=" * 70)

# ============================================
# TEST 1: Environment Variables
# ============================================
print("\n[TEST 1] Checking Environment Variables...")
api_key = os.getenv('GEMINI_API_KEY')
if api_key:
    print(f"✅ GEMINI_API_KEY is set (ends with: ...{api_key[-10:]})")
else:
    print("❌ GEMINI_API_KEY not set!")
    print("Please set it: $env:GEMINI_API_KEY='your-key-here'")
    sys.exit(1)

# ============================================
# TEST 2: RAG System (Vector Database)
# ============================================
print("\n[TEST 2] Testing RAG System (Vector Database)...")
try:
    from rag.retriever import retrieve_context
    
    test_query = "What is a deductible?"
    context = retrieve_context(test_query)
    
    if context and len(context) > 0:
        print(f"✅ RAG retrieval working")
        print(f"   Query: {test_query}")
        print(f"   Context retrieved: {len(context)} characters")
        print(f"   Preview: {context[:150]}...")
    else:
        print("❌ RAG returned empty context")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ RAG System Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================
# TEST 3: LLM System (Gemini)
# ============================================
print("\n[TEST 3] Testing LLM System (Gemini)...")
try:
    from llm.gemini_client import generate_response
    
    test_query = "What is a deductible?"
    test_context = "A deductible is the money you pay first when you file a claim."
    
    response = generate_response(test_query, test_context)
    
    if response and len(response) > 0:
        print(f"✅ LLM generation working")
        print(f"   Query: {test_query}")
        print(f"   Response length: {len(response)} characters")
        print(f"   Preview: {response[:150]}...")
    else:
        print("❌ LLM returned empty response")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ LLM System Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================
# TEST 4: Complete RAG + LLM Pipeline
# ============================================
print("\n[TEST 4] Testing Complete RAG + LLM Pipeline...")
try:
    test_queries = [
        "What is a deductible?",
        "How do I file a claim?",
        "What is subrogation?"
    ]
    
    for query in test_queries:
        # Retrieve context
        context = retrieve_context(query)
        
        # Generate response
        response = generate_response(query, context)
        
        print(f"\n✅ Query: {query}")
        print(f"   Context: {len(context)} chars")
        print(f"   Response: {len(response)} chars")
        print(f"   Answer preview: {response[:100]}...")
        
except Exception as e:
    print(f"❌ Pipeline Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ============================================
# TEST 5: Vector Database Status
# ============================================
print("\n[TEST 5] Checking Vector Database...")
try:
    import chromadb
    from pathlib import Path
    
    db_path = Path("vector_db")
    if db_path.exists():
        print(f"✅ Vector database found at: {db_path.absolute()}")
        
        client = chromadb.PersistentClient(path=str(db_path))
        collection = client.get_collection(name="insurance_kb")
        count = collection.count()
        
        print(f"   Collection: insurance_kb")
        print(f"   Total chunks: {count}")
    else:
        print("❌ Vector database not found!")
        print("   Run: python rag/build_vector_db.py")
        
except Exception as e:
    print(f"⚠️  Could not check database: {e}")

# ============================================
# TEST 6: Knowledge Base Files
# ============================================
print("\n[TEST 6] Checking Knowledge Base Files...")
try:
    from pathlib import Path
    
    kb_path = Path("knowledge_base")
    txt_files = list(kb_path.glob("*.txt"))
    
    if txt_files:
        print(f"✅ Found {len(txt_files)} knowledge base files:")
        for file in txt_files:
            size = file.stat().st_size
            print(f"   - {file.name} ({size:,} bytes)")
    else:
        print("❌ No knowledge base files found!")
        
except Exception as e:
    print(f"⚠️  Could not check knowledge base: {e}")

# ============================================
# TEST 7: Voice Assistant (Optional)
# ============================================
print("\n[TEST 7] Checking Voice Assistant Components...")
try:
    from voice.stt import speech_to_text
    from voice.tts import text_to_speech
    from voice.voice_pipeline import voice_chat
    
    print("✅ Voice Assistant imports successful")
    print("   - STT (Whisper) available")
    print("   - TTS (gTTS) available")
    print("   - Voice pipeline available")
    print("   Note: Voice features require audio files to test")
    
except ImportError as e:
    print(f"⚠️  Voice Assistant not fully available: {e}")
    print("   This is optional - main app will still work")

# ============================================
# FINAL SUMMARY
# ============================================
print("\n" + "=" * 70)
print("INTEGRATION TEST COMPLETE")
print("=" * 70)
print("\n✅ All core components are working!")
print("✅ RAG system can retrieve context")
print("✅ LLM system can generate responses")
print("✅ Complete pipeline tested successfully")
print("\nYour system is ready to run!")
print("\nTo start the app:")
print("  $env:GEMINI_API_KEY='your-key-here'")
print("  streamlit run app.py")
