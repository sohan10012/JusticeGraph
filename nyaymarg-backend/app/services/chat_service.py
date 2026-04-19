"""
app/services/chat_service.py
=============================
Rule-based intent detection with rich template responses.
Architecture is LLM-ready — swap _generate_reply() for an LLM call in v3.0.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.schemas.chat import ChatResponse

# ── Intent keyword map ────────────────────────────────────────────────────────
_INTENTS: dict[str, list[str]] = {
    "predict":  ["predict", "outcome", "will i win", "chance", "result", "judgment", "my case"],
    "search":   ["similar", "precedent", "find cases", "related", "like my case", "past cases"],
    "explain":  ["explain", "what is", "how does", "define", "mean", "tell me about", "works"],
    "stats":    ["accuracy", "how accurate", "model performance", "success rate", "f1", "auc"],
    "court":    ["which court", "best court", "court backlog", "court risk", "court performance"],
    "judge":    ["judge", "justice", "who decides", "who handles", "judicial officer"],
    "laws":     ["law", "section", "ipc", "cpc", "article", "act", "provision", "statute"],
}

_RESPONSES: dict[str, str] = {
    "predict": (
        "I can predict your case outcome using NyayMarg's Random Forest + Logistic Regression "
        "ensemble (RFC 65%, LR 35%). Head to the **Predict** screen, fill in your case details "
        "and judgment text, and get a confidence score in seconds."
    ),
    "search": (
        "NyayMarg's precedent engine uses cosine similarity across 7,000+ indexed cases. "
        "Try **Find Precedents** — just describe your case and we'll rank the most legally "
        "relevant past judgments instantly."
    ),
    "explain": (
        "NyayMarg uses two ML models: a **Random Forest Classifier** for structured court and "
        "case attributes, and **Logistic Regression** on TF-IDF text features extracted from "
        "judgment text. Their predictions are combined in a weighted ensemble (RFC 65%, LR 35%)."
    ),
    "stats": (
        "Our current ensemble achieves approximately **78% accuracy** on held-out test data. "
        "Full metrics — accuracy, F1 score, AUC-ROC, and 5-fold cross-validation — are visible "
        "in the Analytics dashboard under **Model Performance**."
    ),
    "court": (
        "NyayMarg analyses court backlog rates, filing/disposal ratios, and digitisation levels "
        "to classify courts as **Low**, **Moderate**, or **High Risk**. Browse state-wise breakdowns "
        "in the Courts section."
    ),
    "judge": (
        "NyayMarg profiles 300+ judges across India by specialisation, reversal rate, average "
        "judgment time, and bias index. Browse and compare judge profiles in the search panel."
    ),
    "laws": (
        "NyayMarg covers 9 major legal frameworks including IPC, CPC, IT Act, GST Act, "
        "Environment Act, Industrial Disputes Act, and key Constitutional provisions (Articles 14 & 21). "
        "Browse the Laws section for detailed descriptions."
    ),
    "general": (
        "NyayMarg is an AI-powered legal analytics platform for the Indian judiciary. "
        "I can help you:\n"
        "- 🎯 **Predict** case outcomes\n"
        "- 🔍 **Find** similar precedents\n"
        "- 📊 **Analyse** court and judge performance\n"
        "- 📖 **Explain** how our models work\n\n"
        "What would you like to explore?"
    ),
}

_CTA_MAP: dict[str, dict] = {
    "predict": {"label": "Predict My Case",   "route": "/predict"},
    "search":  {"label": "Find Precedents",   "route": "/precedents"},
    "stats":   {"label": "View Analytics",    "route": "/analytics"},
    "court":   {"label": "Explore Courts",    "route": "/courts"},
    "judge":   {"label": "Browse Judges",     "route": "/judges"},
    "laws":    {"label": "Browse Laws",       "route": "/laws"},
}


class ChatService:

    def detect_intent(self, message: str) -> str:
        msg = message.lower()
        for intent, keywords in _INTENTS.items():
            if any(kw in msg for kw in keywords):
                return intent
        return "general"

    def build_cta(self, intent: str) -> dict | None:
        return _CTA_MAP.get(intent)

    async def process(
        self,
        message:    str,
        session_id: str,
        user_id:    uuid.UUID,
        db=None,           # AsyncSession — optional
    ) -> ChatResponse:
        intent = self.detect_intent(message)
        reply  = _RESPONSES.get(intent, _RESPONSES["general"])
        cta    = self.build_cta(intent)
        now    = datetime.now(timezone.utc)

        if db is not None:
            await self._persist(db, user_id, session_id, "user",      message, intent, None)
            await self._persist(db, user_id, session_id, "assistant", reply,   intent, cta)

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            intent=intent,
            cta=cta,
            timestamp=now,
        )

    @staticmethod
    async def _persist(db, user_id, session_id, role, content, intent, cta):
        from app.models.chat_message import ChatMessage
        msg = ChatMessage(
            user_id=user_id,
            session_id=session_id,
            role=role,
            content=content,
            intent=intent,
            cta=cta,
        )
        db.add(msg)
        await db.flush()
