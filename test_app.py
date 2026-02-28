"""
Test script for ClaimFlow AI application
"""

from llm.gemini_client import generate_response

# Default knowledge base context
DEFAULT_CONTEXT = """
INSURANCE CLAIMS WORKFLOW STAGES:

1. CLAIM REGISTRATION:
   - Policyholder reports the incident
   - Unique claim reference number is generated
   - Basic claim information is recorded
   - Timeline: Usually completed within 1 business day

2. DOCUMENT VERIFICATION:
   - Submitted documents (claim forms, invoices, receipts) are reviewed
   - Completeness check: Are all required documents provided?
   - Document authenticity is verified
   - Timeline: 3-5 business days

3. CLAIM ASSESSMENT:
   - Claim officer reviews all submitted information
   - Incident details are evaluated
   - Relevant policy sections are cross-checked
   - Assessment report is prepared
   - Timeline: 5-10 business days

4. SETTLEMENT PROCESSING:
   - Financial calculations are completed
   - Administrative procedures are finalized
   - Settlement approval is processed
   - Payment is initiated
   - Timeline: 2-5 business days after assessment

GENERAL INFORMATION:
- Claims can be made through phone, email, or online portal
- Most insurers have 24/7 claim hotlines
- Claim status can be tracked using the reference number
- Communication updates are typically sent via email or SMS
- Appeal process is available if claim is rejected
"""

# Test queries
test_queries = [
    "What happens in claim registration?",
    "How long does document verification take?",
    "Explain the claim assessment stage",
    "Can you approve my claim?",
    "What documents do I need for a claim?",
]

print("\n" + "="*70)
print("🏢 CLAIMFLOW AI - AUTOMATED TEST SUITE")
print("="*70 + "\n")

for i, query in enumerate(test_queries, 1):
    print(f"\n📋 TEST {i}:")
    print(f"User: {query}")
    print("\nClaimFlow AI:")
    response = generate_response(query, DEFAULT_CONTEXT)
    print(response)
    print("\n" + "-"*70)

print("\n✅ All tests completed successfully!\n")
