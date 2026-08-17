"""Intent detection service for customer support queries."""

import re
from typing import Dict


class IntentDetectionService:
    """Classifies customer support questions into predefined intents."""

    INTENTS = {
        "Billing": [
            "payment",
            "paid",
            "charge",
            "charged",
            "invoice",
            "billing",
            "transaction",
            "card",
        ],
        "Technical": [
            "error",
            "bug",
            "crash",
            "crashing",
            "not working",
            "broken",
            "problem",
            "issue",
            "technical",
            "website",
            "application",
            "app",
        ],
        "Account": [
            "login",
            "log in",
            "sign in",
            "password",
            "account",
            "username",
            "locked",
            "profile",
        ],
        "Refund": [
            "refund",
            "money back",
            "return my money",
            "reimburse",
            "reimbursement",
        ],
    }

    def classify(self, text: str) -> Dict:
        """Classify a support question and return intent + confidence."""

        if not text or not text.strip():
            return {
                "intent": "General",
                "confidence": 0.50,
            }

        text_lower = text.lower().strip()

        scores = {
            intent: 0
            for intent in self.INTENTS
        }

        for intent, keywords in self.INTENTS.items():
            for keyword in keywords:
                if keyword in text_lower:
                    scores[intent] += 1

        best_intent = max(scores, key=scores.get)
        best_score = scores[best_intent]

        if best_score == 0:
            return {
                "intent": "General",
                "confidence": 0.60,
            }

        confidence = min(
            0.95,
            0.70 + (best_score - 1) * 0.10
        )

        return {
            "intent": best_intent,
            "confidence": round(confidence, 2),
        }


intent_service = IntentDetectionService()