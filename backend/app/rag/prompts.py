"""Prompt templates for RAG system."""
from langchain_core.prompts import PromptTemplate


# QA Prompt Template
QA_PROMPT_TEMPLATE = """Based on the provided context, answer the customer's question. 
If the context doesn't contain relevant information, say "I don't have enough information to answer this."

Context:
{context}

Question: {question}

Answer with a helpful and professional response."""

QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=QA_PROMPT_TEMPLATE
)


# Detailed QA Prompt with Instructions
DETAILED_QA_PROMPT_TEMPLATE = """You are a helpful customer support assistant. Use the provided knowledge base context to answer the customer's question accurately and professionally.

Instructions:
1. Use only information from the provided context
2. Be concise but thorough
3. If the context is insufficient, offer to escalate to a human agent
4. Maintain a professional and friendly tone

Knowledge Base Context:
{context}

Customer Question: {question}

Your Answer:"""

DETAILED_QA_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template=DETAILED_QA_PROMPT_TEMPLATE
)


# Confidence Scoring Prompt
CONFIDENCE_PROMPT_TEMPLATE = """Based on the provided context and the question, evaluate your confidence in the answer.
Return a JSON response with:
- confidence_score: (0-1) how confident you are in the answer
- explanation: brief explanation of the confidence level

Context: {context}
Question: {question}
Your Answer: {answer}

Response in JSON format:"""

CONFIDENCE_PROMPT = PromptTemplate(
    input_variables=["context", "question", "answer"],
    template=CONFIDENCE_PROMPT_TEMPLATE
)


# Clarification Prompt
CLARIFICATION_PROMPT_TEMPLATE = """The user asked: "{question}"

Based on the knowledge base context provided, is the question clear enough to answer, 
or does it need clarification?

Context topics: {context}

1. If the question is clear, respond: "CLEAR"
2. If clarification is needed, suggest what should be clarified.

Your assessment:"""

CLARIFICATION_PROMPT = PromptTemplate(
    input_variables=["question", "context"],
    template=CLARIFICATION_PROMPT_TEMPLATE
)


# Follow-up Question Generation Prompt
FOLLOWUP_PROMPT_TEMPLATE = """Based on the question "{question}" and the answer provided, 
suggest 2-3 relevant follow-up questions that might help the customer further.

Format: Return only the questions as a numbered list.

Question: {question}
Answer: {answer}

Follow-up questions:"""

FOLLOWUP_PROMPT = PromptTemplate(
    input_variables=["question", "answer"],
    template=FOLLOWUP_PROMPT_TEMPLATE
)


# Summary Prompt
SUMMARY_PROMPT_TEMPLATE = """Create a concise summary of the following context that could be useful 
for customer support representatives:

Context: {context}

Summary (2-3 sentences):"""

SUMMARY_PROMPT = PromptTemplate(
    input_variables=["context"],
    template=SUMMARY_PROMPT_TEMPLATE
)


# Get all available prompts
AVAILABLE_PROMPTS = {
    "qa": QA_PROMPT,
    "detailed_qa": DETAILED_QA_PROMPT,
    "confidence": CONFIDENCE_PROMPT,
    "clarification": CLARIFICATION_PROMPT,
    "followup": FOLLOWUP_PROMPT,
    "summary": SUMMARY_PROMPT,
}


def get_prompt(prompt_name: str) -> PromptTemplate:
    """
    Get a prompt template by name.
    
    Args:
        prompt_name: Name of the prompt template
    
    Returns:
        PromptTemplate instance
    
    Raises:
        ValueError: If prompt name not found
    """
    if prompt_name not in AVAILABLE_PROMPTS:
        raise ValueError(f"Prompt '{prompt_name}' not found. Available: {list(AVAILABLE_PROMPTS.keys())}")
    return AVAILABLE_PROMPTS[prompt_name]
