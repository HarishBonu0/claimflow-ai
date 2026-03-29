"""Finance-specialized assistant pipeline.

This module separates intent understanding, prompt construction, and response generation
for deterministic, professional-grade financial assistance.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from typing import Any

from llm.gemini_client import (
    _build_model_sequence,
    _is_model_unavailable_error,
    _is_quota_error,
    _map_api_error,
    client,
)

logger = logging.getLogger("claimflow.finance")


SECTION_ORDER = ["Summary", "Explanation", "Actionable Steps", "Example"]

LANGUAGE_FALLBACK_CODE = {
    "english": "en",
    "hindi": "hi",
    "telugu": "te",
    "tamil": "ta",
    "kannada": "kn",
}


@dataclass
class IntentResult:
    intent: str
    confidence: float
    needs_clarification: bool
    clarification_question: str
    risk_sensitive: bool
    in_domain: bool


class FinanceIntentAnalyzer:
    """Intent analysis for finance-focused conversations."""

    INTENT_KEYWORDS = {
        "personal_finance": [
            "personal finance", "salary", "income", "expense", "debt", "loan",
            "cashflow", "money management", "financial habits",
        ],
        "budgeting": [
            "budget", "monthly plan", "expense tracking", "spending", "save money",
            "cut costs", "emergency fund", "50 30 20", "household budget",
        ],
        "investing": [
            "invest", "asset allocation", "portfolio", "mutual fund", "etf", "sip",
            "fixed income", "returns", "long term investing",
        ],
        "stock_market": [
            "stock", "equity", "nifty", "sensex", "share market", "valuation",
            "pe ratio", "earnings", "market trend",
        ],
        "risk_analysis": [
            "risk", "volatility", "drawdown", "downside", "diversification",
            "hedge", "risk tolerance", "scenario analysis",
        ],
        "financial_planning": [
            "financial planning", "retirement", "goal planning", "college fund",
            "insurance planning", "tax planning", "net worth", "long term goals",
        ],
    }

    DOMAIN_HINTS = {
        "finance", "budget", "invest", "investment", "stock", "market", "portfolio",
        "risk", "debt", "loan", "savings", "retirement", "asset", "cashflow", "tax",
        "emergency fund", "mutual fund", "etf", "equity", "bond", "planning",
    }

    RISKY_HINTS = {
        "buy this stock", "guaranteed return", "double money", "all in", "leverage",
        "options trading", "futures", "intraday", "margin", "crypto signal",
    }

    ADVICE_HINTS = {
        "should i", "what should i do", "recommend", "which one", "which should i",
        "is it good", "where should i invest", "how much should i invest",
        "buy or sell", "can i invest", "best option",
    }

    @classmethod
    def analyze(cls, user_input: str) -> IntentResult:
        text = (user_input or "").strip().lower()
        clean = re.sub(r"[^a-z0-9\s]", " ", text)
        clean = re.sub(r"\s+", " ", clean).strip()
        words = set(clean.split())

        has_non_latin = any(ord(ch) > 127 for ch in text)

        if not clean:
            # Avoid forcing clarification when keyword rules cannot parse the message
            # (for example native scripts or encoding-mangled input from clients).
            if text:
                intent_name = "personal_finance"
                if has_non_latin and ("భీమ" in text or "इंश्य" in text or "காப்பீ" in text or "ವಿಮೆ" in text):
                    intent_name = "financial_planning"

                return IntentResult(
                    intent=intent_name,
                    confidence=0.35,
                    needs_clarification=False,
                    clarification_question="",
                    risk_sensitive=False,
                    in_domain=True,
                )

            return IntentResult(
                intent="clarification",
                confidence=0.0,
                needs_clarification=True,
                clarification_question=(
                    "Please share your finance question in one sentence. "
                    "For example, budgeting, investing, stock market, or risk analysis."
                ),
                risk_sensitive=False,
                in_domain=True,
            )

        scores: dict[str, float] = {}
        for intent, keywords in cls.INTENT_KEYWORDS.items():
            score = 0.0
            for keyword in keywords:
                k = keyword.lower()
                if " " in k:
                    if k in clean:
                        score += 1.0
                else:
                    if k in words:
                        score += 1.0
                    elif k in clean:
                        score += 0.6
            scores[intent] = score

        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]
        total_keywords = max(len(cls.INTENT_KEYWORDS.get(best_intent, [])), 1)
        confidence = min(best_score / max(total_keywords * 0.35, 1), 1.0)

        domain_overlap = sum(1 for hint in cls.DOMAIN_HINTS if hint in clean)
        in_domain = domain_overlap > 0 or confidence >= 0.2

        risk_sensitive = best_intent in {"investing", "stock_market", "risk_analysis"}
        if any(hint in clean for hint in cls.RISKY_HINTS):
            risk_sensitive = True

        needs_clarification = False
        clarification_question = ""
        short_query = len(clean.split()) <= 3

        is_advice_query = any(hint in clean for hint in cls.ADVICE_HINTS) or risk_sensitive

        if not in_domain and is_advice_query:
            needs_clarification = True
            clarification_question = (
                "I can help with finance topics only. "
                "Do you want help with budgeting, investing, stock market, risk analysis, "
                "or financial planning?"
            )
        elif is_advice_query and short_query and confidence < 0.15 and domain_overlap == 0:
            needs_clarification = True
            clarification_question = (
                "Could you clarify your goal and time horizon? "
                "For example: monthly budget target, investment amount, and risk comfort."
            )

        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            needs_clarification=needs_clarification,
            clarification_question=clarification_question,
            risk_sensitive=risk_sensitive,
            in_domain=in_domain,
        )


class FinancePromptBuilder:
    """Build deterministic, structured prompts for finance guidance."""

    @staticmethod
    def build(
        user_input: str,
        conversation_history: list[dict[str, str]],
        intent: IntentResult,
        language_name: str,
        context: str,
    ) -> str:
        recent_history = conversation_history[-8:] if conversation_history else []
        history_lines = []
        for msg in recent_history:
            role = "User" if msg.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {msg.get('content', '')}")

        risk_note = ""
        if intent.risk_sensitive:
            risk_note = (
                "Because this query can influence financial risk, include a concise educational "
                "disclaimer and avoid stock-picking or guaranteed-return language."
            )

        return f"""
You are an expert financial assistant focused on practical, accurate, and safe guidance.

Language Rule:
- Respond in {language_name}.

Domain Scope:
- Personal finance, budgeting, investing, stock market, risk analysis, financial planning.
- If uncertain, say so clearly and suggest what data is needed.
- Do not fabricate facts.

Safety Rule:
- Never promise returns.
- Never give absolute buy/sell guarantees.
- Keep guidance educational and risk-aware.
- {risk_note}

Formatting Contract (strict plain text):
- No markdown, no asterisks, no hash symbols.
- Output exactly these sections in order:
Summary
Explanation
Actionable Steps
Example

Section quality requirements:
- Summary: 1 to 2 precise sentences.
- Explanation: focused reasoning, assumptions, and uncertainty if any.
- Actionable Steps: numbered lines starting with 1., 2., 3.
- Example: one compact realistic example or write "Not needed for this query.".

Conversation History:
{os.linesep.join(history_lines) if history_lines else 'None'}

Retrieved Context:
{context if context.strip() else 'No external context found. Use foundational finance principles.'}

Interpreted Intent:
{intent.intent} (confidence={intent.confidence:.2f}, risk_sensitive={intent.risk_sensitive})

Current User Query:
{user_input}
""".strip()


class FinanceResponseGenerator:
    """Generate responses with model fallback and deterministic configuration."""

    @staticmethod
    def generate(prompt: str) -> str:
        model_sequence = _build_model_sequence()
        temperature = float(os.getenv("FINANCE_RESPONSE_TEMPERATURE", "0.15"))
        top_p = float(os.getenv("FINANCE_RESPONSE_TOP_P", "0.8"))
        max_tokens = int(os.getenv("FINANCE_RESPONSE_MAX_TOKENS", "1200"))

        logger.info(
            json.dumps(
                {
                    "event": "finance_model_attempt_order",
                    "models": model_sequence,
                    "temperature": temperature,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                }
            )
        )

        last_error: Exception | None = None
        quota_error: Exception | None = None

        for idx, model_name in enumerate(model_sequence):
            has_next = idx < len(model_sequence) - 1
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "temperature": temperature,
                        "top_p": top_p,
                        "max_output_tokens": max_tokens,
                    },
                )
                text = (getattr(response, "text", "") or "").strip()
                if text:
                    return text
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                logger.error("finance_generation_failed model=%s error=%s", model_name, str(exc)[:500])

                if _is_quota_error(exc):
                    if quota_error is None:
                        quota_error = exc
                    if has_next:
                        continue

                if _is_model_unavailable_error(exc) and has_next:
                    continue

                return _map_api_error(exc)

        if quota_error:
            return _map_api_error(quota_error)
        if last_error:
            return _map_api_error(last_error)
        return "AI service is temporarily unavailable. Please try again later."


def _strip_markdown_symbols(text: str) -> str:
    cleaned = text.replace("*", "").replace("#", "").replace("`", "")
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def _extract_section(content: str, header: str, next_headers: list[str]) -> str:
    pattern = rf"(?im)^\s*{re.escape(header)}\s*:?\s*$"
    match = re.search(pattern, content)
    if not match:
        return ""

    start = match.end()
    end = len(content)
    for nxt in next_headers:
        nxt_match = re.search(rf"(?im)^\s*{re.escape(nxt)}\s*:?\s*$", content[start:])
        if nxt_match:
            end = min(end, start + nxt_match.start())
    return content[start:end].strip()


def enforce_plain_structured_response(raw_text: str) -> str:
    text = _strip_markdown_symbols(raw_text or "")
    if not text:
        text = "I do not have enough information to answer confidently."

    sections: dict[str, str] = {}
    for idx, section in enumerate(SECTION_ORDER):
        next_sections = SECTION_ORDER[idx + 1 :]
        sections[section] = _extract_section(text, section, next_sections)

    if not any(sections.values()):
        sections["Summary"] = text.split("\n")[0][:220].strip() or "No summary available."
        sections["Explanation"] = text.strip()

    if not sections["Actionable Steps"]:
        sections["Actionable Steps"] = (
            "1. Define your financial goal, amount, and timeline.\n"
            "2. Share your risk comfort and current monthly cash flow.\n"
            "3. Reassess the plan every month using actual spending and returns."
        )

    # Ensure numbered actionable steps.
    steps_lines = [line.strip() for line in sections["Actionable Steps"].split("\n") if line.strip()]
    normalized_steps = []
    for i, line in enumerate(steps_lines, start=1):
        line = re.sub(r"^[-•\d\.)\s]+", "", line).strip()
        normalized_steps.append(f"{i}. {line}")
    sections["Actionable Steps"] = "\n".join(normalized_steps) if normalized_steps else "1. No steps provided."

    if not sections["Example"]:
        sections["Example"] = "Not needed for this query."

    # Remove remaining markdown-like list markers.
    for key, value in sections.items():
        val = re.sub(r"\n\s*[-•]\s*", "\n", value)
        sections[key] = val.strip()

    output_lines = []
    for section in SECTION_ORDER:
        output_lines.append(section)
        output_lines.append(sections[section])
        output_lines.append("")

    return "\n".join(output_lines).strip()


def enforce_risk_disclaimer(response_text: str) -> str:
    """Ensure sensitive finance responses include an educational disclaimer."""
    text_lower = response_text.lower()
    if "not financial advice" in text_lower or "educational" in text_lower:
        return response_text

    lines = response_text.split("\n")
    try:
        exp_idx = lines.index("Explanation")
        # Find next section header after Explanation.
        next_idx = len(lines)
        for i in range(exp_idx + 1, len(lines)):
            if lines[i].strip() in SECTION_ORDER:
                next_idx = i
                break
        explanation_block = "\n".join(lines[exp_idx + 1 : next_idx]).strip()
        disclaimer = (
            "This is educational guidance, not personalized financial advice. "
            "Decisions should be validated with your financial advisor based on your risk profile."
        )
        if explanation_block:
            explanation_block = f"{explanation_block} {disclaimer}"
        else:
            explanation_block = disclaimer

        new_lines = lines[: exp_idx + 1] + [explanation_block] + lines[next_idx:]
        return "\n".join(new_lines)
    except ValueError:
        return response_text


def _is_service_error_text(text: str) -> bool:
    lowered = (text or "").lower()
    return (
        "quota exceeded" in lowered
        or "temporarily unavailable" in lowered
        or "no configured gemini model" in lowered
        or "unable to connect" in lowered
    )


def _finance_fallback_response(intent: IntentResult, language_name: str) -> str:
    code = LANGUAGE_FALLBACK_CODE.get((language_name or "").strip().lower(), "en")

    responses = {
        "en": {
            "general": (
                "I can still help while AI service is busy. "
                "Share your income, expenses, goal, and timeline, and I will provide a practical finance plan."
            ),
            "budgeting": (
                "For budgeting, start with this rule: essentials 50%, goals 30%, savings 20%. "
                "Track all spending weekly and adjust categories that exceed limits."
            ),
            "investing": (
                "For investing, begin with diversification and small monthly contributions. "
                "Choose instruments based on risk tolerance, timeline, and emergency fund readiness."
            ),
            "stock_market": (
                "For stock market decisions, avoid guaranteed-return thinking. "
                "Use diversified exposure, defined risk limits, and long-term horizon before increasing allocation."
            ),
            "risk_analysis": (
                "For risk analysis, first define maximum acceptable loss and investment horizon. "
                "Then spread allocation across asset classes to reduce concentration risk."
            ),
            "financial_planning": (
                "For financial planning, define goals by time horizon: short, medium, and long term. "
                "Map monthly savings to each goal and review progress monthly."
            ),
        },
        "hi": {
            "general": "AI सेवा अभी व्यस्त है। आप आय, खर्च, लक्ष्य और समय अवधि बताइए, मैं व्यावहारिक वित्त योजना दूंगा।",
            "budgeting": "बजट के लिए 50-30-20 नियम से शुरू करें। खर्च साप्ताहिक ट्रैक करें और लिमिट से ऊपर जाने वाली श्रेणियां तुरंत कम करें।",
            "investing": "निवेश में विविधीकरण और छोटे मासिक निवेश से शुरू करें। जोखिम क्षमता और समय अवधि के आधार पर विकल्प चुनें।",
            "stock_market": "शेयर बाजार में गारंटीड रिटर्न सोच से बचें। लंबी अवधि और स्पष्ट जोखिम सीमा के साथ निवेश करें।",
            "risk_analysis": "रिस्क विश्लेषण में पहले अधिकतम नुकसान सीमा तय करें। फिर अलग-अलग एसेट क्लास में निवेश बांटें।",
            "financial_planning": "वित्तीय योजना के लिए लक्ष्यों को समय अवधि के अनुसार बांटें और हर महीने प्रगति की समीक्षा करें।",
        },
        "te": {
            "general": "AI సేవ ప్రస్తుతం బిజీగా ఉంది. మీ ఆదాయం, ఖర్చులు, లక్ష్యం, కాలవ్యవధి చెప్తే నేను ప్రాక్టికల్ ఫైనాన్స్ ప్లాన్ ఇస్తాను.",
            "budgeting": "బడ్జెట్ కోసం 50-30-20 విధానంతో ప్రారంభించండి. ప్రతి వారం ఖర్చులను ట్రాక్ చేసి, ఎక్కువైన ఖర్చులను తగ్గించండి.",
            "investing": "ఇన్వెస్టింగ్‌ను చిన్న నెలసరి మొత్తాలతో, డైవర్సిఫికేషన్‌తో ప్రారంభించండి. రిస్క్ సామర్థ్యం మరియు టైమ్ హరైజన్ ఆధారంగా ఎంపిక చేయండి.",
            "stock_market": "స్టాక్ మార్కెట్‌లో గ్యారంటీ రిటర్న్స్ అనుకోవద్దు. దీర్ఘకాల దృష్టి మరియు స్పష్టమైన రిస్క్ లిమిట్స్‌తో ముందుకు వెళ్లండి.",
            "risk_analysis": "రిస్క్ విశ్లేషణలో ముందుగా అంగీకరించే గరిష్ట నష్టాన్ని నిర్ణయించండి. తర్వాత పెట్టుబడిని విభిన్న ఆస్తుల్లో విభజించండి.",
            "financial_planning": "ఫైనాన్షియల్ ప్లానింగ్ కోసం లక్ష్యాలను కాలవ్యవధి ప్రకారం విభజించి, ప్రతి నెల ప్రోగ్రెస్‌ను సమీక్షించండి.",
        },
        "ta": {
            "general": "AI சேவை இப்போது பிஸியாக உள்ளது. உங்கள் வருமானம், செலவு, இலக்கு, காலவரை சொன்னால் நான் நடைமுறை நிதி திட்டம் தருகிறேன்.",
            "budgeting": "பட்ஜெட்டுக்கு 50-30-20 முறையில் தொடங்குங்கள். வாரந்தோறும் செலவை கண்காணித்து, அதிகமாகும் பிரிவுகளை குறையுங்கள்.",
            "investing": "மாதாந்திர சிறு முதலீடு மற்றும் பரவலாக்கத்துடன் தொடங்குங்கள். உங்கள் அபாய சகிப்பு மற்றும் காலவரைக்கு ஏற்ற கருவிகளைத் தேர்வுசெய்யுங்கள்.",
            "stock_market": "பங்குச் சந்தையில் உறுதியான வருமானம் என்ற எண்ணத்தை தவிர்க்கவும். நீண்டகால நோக்கு மற்றும் தெளிவான அபாய வரம்புடன் செல்லுங்கள்.",
            "risk_analysis": "அபாய மதிப்பீட்டில் முதலில் ஏற்கக்கூடிய அதிகபட்ச இழப்பை நிர்ணயிக்கவும். பின்னர் முதலீட்டை பல சொத்து வகைகளில் பகிரவும்.",
            "financial_planning": "நிதித் திட்டத்தில் இலக்குகளை காலவரையின்படி பிரித்து, மாதந்தோறும் முன்னேற்றத்தை மதிப்பாய்வு செய்யுங்கள்.",
        },
        "kn": {
            "general": "AI ಸೇವೆ ಈಗ ಬ್ಯುಸಿ ಇದೆ. ನಿಮ್ಮ ಆದಾಯ, ಖರ್ಚು, ಗುರಿ ಮತ್ತು ಅವಧಿ ಹೇಳಿದರೆ ನಾನು ಪ್ರಾಯೋಗಿಕ ಹಣಕಾಸು ಯೋಜನೆ ನೀಡುತ್ತೇನೆ.",
            "budgeting": "ಬಜೆಟ್‌ಗೆ 50-30-20 ವಿಧಾನದಿಂದ ಪ್ರಾರಂಭಿಸಿ. ವಾರವಾರ ಖರ್ಚು ಟ್ರ್ಯಾಕ್ ಮಾಡಿ, ಮಿತಿಯನ್ನು ಮೀರಿದ ಖರ್ಚುಗಳನ್ನು ಕಡಿತಗೊಳಿಸಿ.",
            "investing": "ಸಣ್ಣ ಮಾಸಿಕ ಹೂಡಿಕೆ ಮತ್ತು ವಿಭಜನೆಯಿಂದ ಆರಂಭಿಸಿ. ನಿಮ್ಮ ಅಪಾಯ ಸಾಮರ್ಥ್ಯ ಮತ್ತು ಅವಧಿಗೆ ತಕ್ಕ ಆಯ್ಕೆಯನ್ನು ಮಾಡಿ.",
            "stock_market": "ಶೇರು ಮಾರುಕಟ್ಟೆಯಲ್ಲಿ ಖಚಿತ ಲಾಭದ ನಿರೀಕ್ಷೆ ಬೇಡ. ದೀರ್ಘಾವಧಿ ದೃಷ್ಟಿ ಮತ್ತು ಸ್ಪಷ್ಟ ಅಪಾಯ ಮಿತಿಗಳೊಂದಿಗೆ ಹೂಡಿಕೆ ಮಾಡಿ.",
            "risk_analysis": "ಅಪಾಯ ವಿಶ್ಲೇಷಣೆಯಲ್ಲಿ ಮೊದಲು ಗರಿಷ್ಠ ಒಪ್ಪಬಹುದಾದ ನಷ್ಟವನ್ನು ನಿಗದಿಪಡಿ. ನಂತರ ಹೂಡಿಕೆಯನ್ನು ವಿವಿಧ ಆಸ್ತಿ ವರ್ಗಗಳಿಗೆ ಹಂಚಿ.",
            "financial_planning": "ಹಣಕಾಸು ಯೋಜನೆಗಾಗಿ ಗುರಿಗಳನ್ನು ಅವಧಿ ಆಧಾರದ ಮೇಲೆ ವಿಭಾಗಿಸಿ, ಪ್ರತಿಮಾಸ ಪ್ರಗತಿಯನ್ನು ಪರಿಶೀಲಿಸಿ.",
        },
    }

    lang_pack = responses.get(code, responses["en"])
    return lang_pack.get(intent.intent, lang_pack["general"])


def generate_finance_response(
    user_input: str,
    conversation_history: list[dict[str, str]],
    language_name: str = "English",
) -> tuple[str, IntentResult]:
    """End-to-end finance response generation with observability and strict formatting."""
    intent = FinanceIntentAnalyzer.analyze(user_input)

    logger.info(
        json.dumps(
            {
                "event": "finance_intent_interpreted",
                "intent": intent.intent,
                "confidence": round(intent.confidence, 3),
                "needs_clarification": intent.needs_clarification,
                "risk_sensitive": intent.risk_sensitive,
                "in_domain": intent.in_domain,
                "query_preview": user_input[:180],
            }
        )
    )

    if intent.needs_clarification:
        clarification = (
            "Summary\n"
            "I need one more detail before giving a precise finance answer.\n\n"
            "Explanation\n"
            f"{intent.clarification_question}\n\n"
            "Actionable Steps\n"
            "1. Share your goal.\n"
            "2. Share your time horizon.\n"
            "3. Share your risk comfort level.\n\n"
            "Example\n"
            "Goal: Build an emergency fund in 6 months with low risk."
        )
        return clarification, intent

    context = ""
    try:
        # Lazy import keeps deployment resilient when optional RAG deps are unavailable.
        from rag.retriever import retrieve_context

        context = retrieve_context(user_input, k=4, lang="all")
    except ImportError as exc:
        logger.warning("finance_context_retrieval_unavailable: %s", str(exc)[:300])
        context = ""
    except Exception as exc:  # noqa: BLE001
        logger.warning("finance_context_retrieval_failed: %s", str(exc)[:300])

    prompt = FinancePromptBuilder.build(
        user_input=user_input,
        conversation_history=conversation_history,
        intent=intent,
        language_name=language_name,
        context=context,
    )

    raw_response = FinanceResponseGenerator.generate(prompt)

    if _is_service_error_text(raw_response):
        fallback = _finance_fallback_response(intent, language_name)
        logger.info(
            json.dumps(
                {
                    "event": "finance_service_fallback_used",
                    "intent": intent.intent,
                    "language": language_name,
                    "response_preview": fallback[:180],
                }
            )
        )
        return fallback, intent

    final_response = enforce_plain_structured_response(raw_response)
    if intent.risk_sensitive:
        final_response = enforce_risk_disclaimer(final_response)

    logger.info(
        json.dumps(
            {
                "event": "finance_response_generated",
                "intent": intent.intent,
                "response_preview": final_response[:240],
            }
        )
    )

    return final_response, intent
