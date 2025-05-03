# models/__init__.py - Exporta os esquemas Pydantic
from .schemas import (
    MessageRole,
    Message,
    Conversation,
    ConversationResponse,
    HealthResponse
)

__all__ = [
    'MessageRole',
    'Message',
    'Conversation',
    'ConversationResponse',
    'HealthResponse'
]
