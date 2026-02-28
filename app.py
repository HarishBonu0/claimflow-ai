# Application entry point

"""
ClaimFlow AI - Insurance Claims Process Explainer
Interactive CLI for asking questions about insurance claim workflows.
"""

from llm.gemini_client import generate_response


# ===============================
# DEFAULT KNOWLEDGE BASE CONTEXT
# ===============================

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


# ===============================
# MAIN CLI APPLICATION
# ===============================

def main():
    """
    Main CLI application for ClaimFlow AI.
    Allows users to ask questions about insurance claims interactively.
    """
    print("\n" + "="*60)
    print("🏢 CLAIMFLOW AI - Insurance Claims Explainer")
    print("="*60)
    print("\nWelcome! I can explain insurance claim processes.")
    print("Ask any question about claim workflows.\n")
    print("Type 'exit' or 'quit' to exit the application.\n")
    print("="*60 + "\n")

    while True:
        # Get user input
        user_query = input("You: ").strip()

        # Check for exit commands
        if user_query.lower() in ["exit", "quit", "bye", "q"]:
            print("\n" + "="*60)
            print("Thank you for using ClaimFlow AI!")
            print("="*60 + "\n")
            break

        # Skip empty queries
        if not user_query:
            print("Please enter a valid question.\n")
            continue

        # Generate response using LLM module
        print("\nClaimFlow AI:")
        response = generate_response(user_query, DEFAULT_CONTEXT)
        print(response)
        print("\n" + "-"*60 + "\n")


# ===============================
# ENTRY POINT
# ===============================

if __name__ == "__main__":
    main()

