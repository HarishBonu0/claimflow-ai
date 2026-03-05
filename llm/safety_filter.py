"""
Safety Filter Module
Pre-LLM guardrails to prevent prohibited queries from reaching the model.
"""

import re


class SafetyFilter:
    """Safety guardrails for insurance and financial queries"""
    
    # Prohibited query patterns
    PROHIBITED_PATTERNS = {
        'claim_approval': [
            r'\b(approve|accept|pass)\s+(my|this|the)\s+claim\b',
            r'\bwill\s+(my|this|the)\s+claim\s+(be\s+)?(approved|accepted|pass)\b',
            r'\bshould\s+(you|i|we)\s+approve\b',
            r'\bcan\s+(you|i)\s+(approve|accept)\b',
        ],
        'coverage_decision': [
            r'\bwhich\s+insurance\s+(should|must|to)\s+(i|we)\s+buy\b',
            r'\brecommend\s+(me\s+)?(an?\s+)?insurance\b',
            r'\bbest\s+insurance\s+(for|to)\b',
            r'\btell\s+me\s+what\s+insurance\b',
        ],
        'financial_advice': [
            r'\bshould\s+i\s+invest\s+in\b',
            r'\brecommend\s+(stocks?|mutual\s+funds?|shares?)\b',
            r'\bwhich\s+(stock|fund|share)\s+to\s+buy\b',
            r'\bguaranteed?\s+returns?\b',
            r'\btell\s+me\s+where\s+to\s+invest\b',
        ],
        'legal_advice': [
            r'\bcan\s+i\s+sue\b',
            r'\blegal\s+action\s+against\b',
            r'\bhire\s+(a\s+)?lawyer\b',
            r'\bwhat\s+are\s+my\s+legal\s+rights\b',
        ],
        'personal_decision': [
            r'\bshould\s+i\s+(file|submit|make)\s+(a\s+)?claim\b',
            r'\btell\s+me\s+(what|whether)\s+to\s+do\b',
            r'\bmake\s+(the\s+)?decision\s+for\s+me\b',
        ]
    }
    
    @staticmethod
    def check_query(query: str) -> tuple[bool, str, str]:
        """
        Check if query is safe to process.
        
        Args:
            query: User's input query
        
        Returns:
            (is_safe, violation_type, reason)
        """
        query_lower = query.lower()
        
        # Check each category
        for category, patterns in SafetyFilter.PROHIBITED_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    return False, category, SafetyFilter._get_rejection_message(category)
        
        return True, "safe", ""
    
    @staticmethod
    def _get_rejection_message(violation_type: str) -> str:
        """Get appropriate rejection message for violation type"""
        
        messages = {
            'claim_approval': """
⚠️ **I Cannot Make Claim Decisions**

I'm designed to **explain** insurance processes, not to approve or reject claims.

**I can help you understand:**
- How claim assessment works
- What factors insurance companies consider
- Required documentation
- Typical timelines

**For claim decisions:** Please contact your insurance provider directly.
""",
            'coverage_decision': """
⚠️ **I Cannot Recommend Insurance Products**

I can **explain** different types of insurance and how they work, but I cannot recommend specific products.

**I can help you understand:**
- Types of insurance coverage
- How deductibles work
- What factors affect premiums
- General coverage concepts

**For product recommendations:** Consult with a licensed insurance agent.
""",
            'financial_advice': """
⚠️ **I Cannot Provide Investment Advice**

I'm here for **educational purposes only**, not to recommend investments.

**I can explain:**
- How compound interest works
- Different asset types (FD, PPF, etc.)
- Savings strategies (general concepts)
- Government schemes (informational)

**For investment advice:** Consult a certified financial advisor.

*This is educational information only, not financial advice.*
""",
            'legal_advice': """
⚠️ **I Cannot Provide Legal Advice**

Legal matters require professional legal counsel.

**I can explain:**
- Standard insurance claim procedures
- Insurance company processes
- Appeals mechanisms (general info)

**For legal guidance:** Consult with a qualified attorney.
""",
            'personal_decision': """
⚠️ **I Cannot Make Personal Decisions**

I can provide **information** to help you understand your options, but the decision is yours.

**I can help with:**
- Explaining your options
- Describing typical processes
- Clarifying terms and concepts

**Your decision:** Talk to your insurance provider or advisor for personalized guidance.
"""
        }
        
        return messages.get(violation_type, "⚠️ I cannot assist with this type of request.")


def check_safety(query: str) -> tuple[bool, str]:
    """
    Quick safety check function.
    
    Args:
        query: User input
    
    Returns:
        (is_safe, rejection_message)
    """
    is_safe, violation_type, message = SafetyFilter.check_query(query)
    return is_safe, message


if __name__ == "__main__":
    # Test safety filter
    print("=" * 70)
    print("Safety Filter Tests")
    print("=" * 70)
    
    test_queries = [
        ("What is a deductible?", True),
        ("Will my claim be approved?", False),
        ("Which insurance should I buy?", False),
        ("Should I invest in stocks?", False),
        ("How does the claim process work?", True),
        ("Can I sue my insurance company?", False),
        ("Explain compound interest", True),
        ("Recommend me a mutual fund", False),
        ("Should I file a claim?", False),
        ("What are government savings schemes?", True),
    ]
    
    for query, expected_safe in test_queries:
        is_safe, message = check_safety(query)
        status = "✅ PASS" if (is_safe == expected_safe) else "❌ FAIL"
        safety_status = "SAFE" if is_safe else "BLOCKED"
        
        print(f"\n{status} | {safety_status}")
        print(f"Query: {query}")
        if not is_safe:
            print(f"Reason: {message[:100]}...")
