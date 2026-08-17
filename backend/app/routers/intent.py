"""API routes for customer support intent detection."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.intent_service import intent_service


router = APIRouter(
    prefix="/intent",
    tags=["intent"],
)


class IntentRequest(BaseModel):
    text: str


class IntentResponse(BaseModel):
    intent: str
    confidence: float


@router.post("/classify", response_model=IntentResponse)
def classify_intent(request: IntentRequest):
    """Classify a customer support question into an intent."""

    result = intent_service.classify(request.text)

    return IntentResponse(
        intent=result["intent"],
        confidence=result["confidence"],
    )