"""
Modelos de dados (DTOs) para o Service2.

Este módulo contém todos os modelos Pydantic utilizados para validação
de dados de entrada/saída da API. Seguimos o DTO (Data Transfer Object)
pattern para garantir validação e documentação automática.
"""
from enum import Enum
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    """Enumeração dos possíveis papéis em uma mensagem."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Modelo para uma mensagem individual na conversação."""

    role: MessageRole = Field(
        description="O papel do remetente da mensagem"
    )
    content: str = Field(
        description="O conteúdo textual da mensagem",
        min_length=1
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "role": "user",
            "content": "Olá, qual é o cardápio do dia?"
        }
    })


class Conversation(BaseModel):
    """Modelo para uma conversa completa."""

    conversation: List[Message] = Field(
        description="Lista de mensagens que compõem a conversa",
        min_length=1
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "conversation": [
                {"role": "user", "content": "Olá, qual é o cardápio do dia?"}
            ]
        }
    })


class ConversationResponse(BaseModel):
    """Modelo para a resposta de uma conversação processada."""

    id: str = Field(description="ID da conversação")
    reply: str = Field(description="Resposta gerada pelo sistema")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados adicionais da resposta"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "conv_123",
            "reply": "Hoje nosso cardápio especial inclui...",
            "metadata": {"processing_time_ms": 250}
        }
    })


class HealthResponse(BaseModel):
    """Modelo para a resposta do health check."""

    status: str = Field(description="Status do serviço")
    components: Dict[str, Dict[str, Any]] = Field(
        description="Status dos componentes do serviço"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "components": {
                "database": {"status": "connected", "latency_ms": 15},
                "vector_store": {"status": "operational", "doc_count": 1000}
            }
        }
    })
