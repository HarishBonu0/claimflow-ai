"""
Intent Classifier Module
Classifies user queries into categories for routing and validation.
"""


class IntentClassifier:
    """Classify user queries into intent categories"""
    
    INTENT_KEYWORDS = {
        'insurance_claim': [
            'claim', 'filing', 'submit', 'process', 'stages', 'assessment',
            'denial', 'reject', 'appeal', 'delay', 'timeline', 'document',
            'status', 'track', 'approved', 'deductible', 'coverage', 'premium',
            'settlement', 'payout', 'reimbursement', 'fraud', 'investigation'
        ],
        'financial_literacy': [
            'savings', 'invest', 'compound', 'interest', 'growth', 'asset',
            'income', 'money', 'ppf', 'apy', 'nps', 'fd', 'fixed deposit',
            'mutual fund', 'scheme', 'plan', 'retire', 'pension', 'inflation',
            'budget', 'emergency fund', '5 year', 'wealth', 'portfolio'
        ],
        'insurance_general': [
            'insurance', 'policy', 'insurer', 'insured', 'beneficiary',
            'health insurance', 'car insurance', 'life insurance', 'term insurance',
            'subrogation', 'co-insurance', 'co-payment', 'exclusion', 'rider'
        ],
        'prohibited': [
            'approve my', 'will my claim', 'should i buy', 'recommend insurance',
            'which insurance', 'best insurance', 'guarantee', 'which stock',
            'should i invest', 'legal action', 'sue', 'lawyer', 'make decision for me'
        ]
    }
    
    @staticmethod
    def classify(query: str) -> tuple[str, float]:
        """
        Classify user query into intent category.
        
        Args:
            query: User's input query
        
        Returns:
            (intent_category, confidence_score)
        """
        query_lower = query.lower()
        
        # Check for prohibited intent first
        prohibited_score = IntentClassifier._calculate_score(query_lower, 'prohibited')
        if prohibited_score > 0.3:
            return 'prohibited', prohibited_score
        
        # Calculate scores for each category
        scores = {}
        for intent, keywords in IntentClassifier.INTENT_KEYWORDS.items():
            if intent != 'prohibited':
                scores[intent] = IntentClassifier._calculate_score(query_lower, intent)
        
        # Return category with highest score
        if scores:
            best_intent = max(scores, key=scores.get)
            confidence = scores[best_intent]
            
            # If confidence too low, mark as general query
            if confidence < 0.2:
                return 'general', 0.5
            
            return best_intent, confidence
        
        return 'general', 0.5
    
    @staticmethod
    def _calculate_score(query: str, intent: str) -> float:
        """Calculate relevance score for intent category"""
        keywords = IntentClassifier.INTENT_KEYWORDS.get(intent, [])
        if not keywords:
            return 0.0
        
        matches = sum(1 for keyword in keywords if keyword in query)
        return min(matches / len(keywords) * 2, 1.0)  # Normalize and cap at 1.0
    
    @staticmethod
    def get_intent_info(intent: str) -> dict:
        """Get metadata about intent category"""
        intent_info = {
            'insurance_claim': {
                'category': 'Insurance Query',
                'description': 'Questions about insurance claims process',
                'safe': True
            },
            'financial_literacy': {
                'category': 'Financial Education',
                'description': 'Questions about savings and financial concepts',
                'safe': True
            },
            'insurance_general': {
                'category': 'Insurance Concepts',
                'description': 'General insurance terminology and concepts',
                'safe': True
            },
            'prohibited': {
                'category': 'Prohibited Query',
                'description': 'Request for advice/decisions outside scope',
                'safe': False
            },
            'general': {
                'category': 'General Query',
                'description': 'General information request',
                'safe': True
            }
        }
        
        return intent_info.get(intent, intent_info['general'])


if __name__ == "__main__":
    # Test intent classifier
    print("=" * 70)
    print("Intent Classifier Tests")
    print("=" * 70)
    
    test_queries = [
        "What is a deductible?",
        "How long does a claim take?",
        "Explain compound interest",
        "What is PPF scheme?",
        "Will my claim be approved?",
        "Which insurance should I buy?",
        "How to file a claim?",
        "Show me savings growth",
        "Should I invest in mutual funds?",
    ]
    
    for query in test_queries:
        intent, confidence = IntentClassifier.classify(query)
        info = IntentClassifier.get_intent_info(intent)
        
        print(f"\nQuery: {query}")
        print(f"Intent: {intent} ({confidence:.2f} confidence)")
        print(f"Category: {info['category']}")
        print(f"Safe: {'✅' if info['safe'] else '❌'}")
