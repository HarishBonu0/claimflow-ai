"""
Insurance Knowledge Base - Contains all educational content
"""


class InsuranceKnowledgeBase:
    """Central knowledge base for insurance and financial literacy"""
    
    @staticmethod
    def get_claims_process() -> str:
        """Return information about insurance claims process"""
        return """**Understanding the Insurance Claims Process**

The insurance claims process typically involves these key stages:

**1. 📝 Claim Filing**
   - Report the incident to your insurance company
   - Provide initial details and policy information
   - Receive a claim reference number

**2. 🔍 Initial Review**
   - Insurer reviews your claim submission
   - Verifies policy coverage and validity
   - Assigns a claims adjuster

**3. 📋 Documentation Collection**
   - Submit required supporting documents
   - Medical reports, bills, police reports (as applicable)
   - Photos, receipts, and other evidence

**4. 🔎 Investigation & Assessment**
   - Claims adjuster reviews all materials
   - May conduct site visits or interviews
   - Determines claim validity and amount

**5. ✅ Decision & Settlement**
   - Claim approved, denied, or partially approved
   - Settlement amount communicated
   - Payment processed

**6. 💰 Payment**
   - Funds disbursed to your account
   - Typically within 7-30 days after approval

💡 **Pro Tip:** Keep all communication documented and respond promptly to requests for additional information to avoid delays.
"""
    
    @staticmethod
    def get_documentation_info() -> str:
        """Return information about required documents"""
        return """**Documents Required for Insurance Claims**

Depending on your claim type, you'll typically need:

**📄 General Documents (Always Required)**
- Policy document copy
- Claim form (duly filled)
- Identity proof (Aadhar, PAN, etc.)
- Bank account details

**🏥 Health Insurance Claims**
- Hospitalization bills and receipts
- Discharge summary
- Doctor's prescriptions
- Medical reports and test results
- Pharmacy bills

**🚗 Vehicle Insurance Claims**
- FIR (for theft/accidents)
- Driving license copy
- RC (Registration Certificate)
- Repair estimates
- Photos of damage

**🏠 Home Insurance Claims**
- Police report (if applicable)
- Photos/videos of damage
- Repair quotations
- Purchase receipts of damaged items

**✈️ Travel Insurance Claims**
- Tickets and boarding passes
- Medical bills (if health-related)
- Proof of cancelled bookings
- Police report (for theft/loss)

📌 **Important:** Keep ORIGINAL copies safe. Submit clear photocopies or scanned PDFs. Always get acknowledgment receipts.
"""
    
    @staticmethod
    def get_delay_reasons() -> str:
        """Return information about common claim delays"""
        return """**Why Is My Claim Taking So Long?**

Common reasons for claim delays include:

**⏱️ Documentation Issues (50% of delays)**
- Incomplete paperwork
- Poor quality scans/photos
- Missing signatures
- Incorrect information

**🔍 Investigation Requirements**
- Complex cases need detailed review
- Large claim amounts trigger extra scrutiny
- Suspected fraud investigations
- Third-party verifications needed

**📋 Policy Coverage Verification**
- Checking if incident is covered
- Reviewing policy terms and exclusions
- Waiting period verifications

**🏥 Medical Assessments**
- Need for independent medical opinion
- Waiting for medical reports
- Pre-existing condition verification

**💼 Administrative Backlogs**
- High claim volumes (seasonal)
- Staff shortages
- System upgrades or technical issues

**🎯 How to Speed Things Up:**

✅ Submit complete documents from day one
✅ Respond immediately to insurer requests
✅ Follow up every 3-5 days politely
✅ Escalate to grievance cell if needed
✅ Keep all communication in writing

⚡ **Expected Timelines:**
- Simple claims: 7-15 days
- Moderate complexity: 15-30 days
- Complex claims: 30-90 days

💡 **Pro Tip:** Use your claim reference number for all follow-ups!
"""
    
    @staticmethod
    def get_tracking_info() -> str:
        """Return information about tracking claims"""
        return """**How to Track Your Insurance Claim Status**

**📱 Online Tracking Methods:**

1. **Company Portal/Website**
   - Log in with policy number
   - Navigate to "My Claims"
   - View real-time status updates

2. **Mobile App**
   - Most insurers have dedicated apps
   - Push notifications for updates
   - Document upload feature

3. **SMS Service**
   - Send claim number to insurer's SMS number
   - Receive instant status reply

4. **Email**
   - Email claims department with reference number
   - Expect response within 24-48 hours

5. **Customer Service**
   - Call toll-free helpline
   - Have your claim reference handy

**🔔 Status Indicators Explained:**

- **"Under Review"** → Documents being checked
- **"Additional Info Required"** → Action needed from you
- **"Investigation"** → Detailed assessment ongoing
- **"Approved"** → Claim accepted, payment pending
- **"Settled"** → Payment processed
- **"Rejected"** → Claim denied (reason will be stated)

**⚠️ If Claim Is Stuck:**

1. Write to grievance officer
2. Escalate to IRDAI ombudsman (after 30 days)
3. File complaint on IRDAI portal

📞 **IRDAI Helpline:** 155255 (Toll-free)
"""
    
    @staticmethod
    def get_savings_info() -> str:
        """Return information about savings and compound growth"""
        return """**Understanding Savings Growth & Compound Interest**

**💰 The Power of Compound Interest**

Compound interest means earning returns on your returns. It's called the "8th wonder of the world" for good reason!

**📊 Basic Formula:**
```
A = P(1 + r/n)^(nt)
```
Where:
- A = Final amount
- P = Principal (initial investment)
- r = Annual interest rate
- n = Compounding frequency
- t = Time in years

**🎯 Example: ₹10,000 invested at 8% annually**

| Years | Simple Interest | Compound Interest | Difference |
|-------|----------------|-------------------|------------|
| 5     | ₹14,000       | ₹14,693          | ₹693      |
| 10    | ₹18,000       | ₹21,589          | ₹3,589    |
| 20    | ₹26,000       | ₹46,610          | ₹20,610   |
| 30    | ₹34,000       | ₹1,00,627        | ₹66,627   |

**🚀 Key Insights:**

✅ **Start Early:** Even small amounts grow significantly over time
✅ **Stay Consistent:** Regular contributions accelerate growth
✅ **Be Patient:** Compound interest needs time to work its magic
✅ **Reinvest Returns:** Don't withdraw; let it compound

**💡 Investment Options in India:**

- **PPF:** 7.1% (Safe, tax-free, 15 years lock-in)
- **FD:** 6-7.5% (Low risk, flexible tenure)
- **Mutual Funds:** 10-12% (Moderate risk, market-linked)
- **Equity:** 12-15%+ (High risk, long-term wealth)

⚠️ **Disclaimer:** Past returns don't guarantee future results. Consult a financial advisor for personalized advice.
"""
    
    @staticmethod
    def get_guardrail_response() -> str:
        """Return guardrail response for sensitive questions"""
        return """**⚠️ Important Notice**

I appreciate your question, but I must clarify my role:

**What I CAN do for you:**
✅ Explain insurance processes in simple terms
✅ Help you understand claim stages
✅ Educate about financial concepts
✅ Answer general "how-to" questions

**What I CANNOT do:**
❌ Predict if your claim will be approved
❌ Recommend specific insurance products
❌ Provide personalized financial advice
❌ Access your policy details
❌ Make decisions on your behalf

**🎯 For Specific Advice:**

If you need decisions about:
- Buying insurance → Contact licensed insurance agent
- Claim approval → Speak with your insurer's claims team
- Investment choices → Consult SEBI-registered financial advisor
- Legal matters → Seek legal counsel

**💡 I'm here to educate and empower you with knowledge!**

How can I help you understand insurance or savings concepts better?
"""
    
    @staticmethod
    def get_default_response() -> str:
        """Return default response for unmatched queries"""
        return """**Thank you for your question!**

I'm ClaimFlow AI, your insurance and financial literacy assistant. I can help you with:

**📋 Insurance Claims:**
- Understanding the claims process
- Required documentation
- Tracking your claim
- Common delay reasons

**💰 Financial Planning:**
- Savings growth and compound interest
- Basic investment concepts
- Financial literacy education

**🎯 How to Ask:**

Try questions like:
- "What documents do I need for a health insurance claim?"
- "Why is my claim taking so long?"
- "Show me how savings grow over time"
- "Explain the claims process step by step"

**Need something specific?** Just ask, and I'll do my best to guide you!

💡 **Remember:** I provide educational guidance only. For decisions about your policy or claims, please contact your insurance provider directly.
"""
