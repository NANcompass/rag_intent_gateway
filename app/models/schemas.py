"""
Pydantic v2 models for RAG Intent Gateway.
"""
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class IntentType(str, Enum):
    """Intent type enumeration."""
    RAG = "RAG"
    CHITCHAT = "CHITCHAT"


class HistoryMessage(BaseModel):
    """Chat history message model."""
    role: str = Field(..., description="Message role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class IntentRequest(BaseModel):
    """Request model for intent processing."""
    query: str = Field(..., description="Current user query", min_length=1)
    history: List[HistoryMessage] = Field(
        default_factory=list,
        description="List of historical chat messages"
    )


class IntentResponse(BaseModel):
    """Structured response from LLM intent analysis."""
    intent_type: IntentType = Field(..., description="Intent classification: RAG or CHITCHAT")
    reason: str = Field(..., description="Brief reason for intent classification")
    reply_text: str = Field(
        default="",
        description="Direct reply for CHITCHAT intent, empty for RAG intent"
    )
    standalone_query: str = Field(
        ...,
        description="Context-resolved standalone query"
    )
    sub_queries: List[str] = Field(
        default_factory=list,
        description="Sub-queries for complex questions"
    )
    expanded_queries: List[str] = Field(
        default_factory=list,
        description="Synonym expanded queries for better retrieval"
    )


class APIResponse(BaseModel):
    """API response wrapper for the intent processing endpoint."""
    success: bool = Field(..., description="Whether the processing was successful")
    data: Optional[IntentResponse] = Field(None, description="Intent analysis result")
    message: str = Field(default="", description="Response message")