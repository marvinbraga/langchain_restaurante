"""
Modelos de dados (DTOs) e esquemas para o Service3.

Este módulo contém todos os modelos Pydantic utilizados para validação
de dados, incluindo o estado do agente ReAct.
"""
from enum import Enum
from typing import List, Dict, Any, Optional, Annotated

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field, ConfigDict
from typing_extensions import TypedDict


class MessageRole(str, Enum):
    """Enumeração dos possíveis papéis em uma mensagem."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """Modelo para uma mensagem individual na conversação."""

    role: MessageRole = Field(description="O papel do remetente da mensagem")
    content: str = Field(description="O conteúdo textual da mensagem", min_length=1)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "role": "user",
            "content": "Quais são as opções vegetarianas?"
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
                {"role": "user", "content": "Quais são as opções vegetarianas?"}
            ]
        }
    })


class ReActState(TypedDict):
    """Estado tipado para o agente ReAct."""
    messages: Annotated[List[AnyMessage], add_messages]


class AgentResponse(BaseModel):
    """Modelo para resposta do agente."""

    id: str = Field(description="ID da conversação")
    reply: str = Field(description="Resposta gerada pelo agente")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Metadados da resposta (tempo de processamento, tools usadas, etc.)"
    )

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "conv_123",
            "reply": "Nossas opções vegetarianas incluem...",
            "metadata": {
                "processing_time_ms": 1250,
                "tools_used": ["search_restaurant_information", "provide_menu_suggestions"]
            }
        }
    })


class DebugStep(BaseModel):
    """Modelo para um passo do debug do agente."""

    node: str = Field(description="Nome do nó processado")
    messages: List[Dict[str, Any]] = Field(description="Estado das mensagens neste passo")
    processing_time_ms: Optional[float] = Field(default=None, description="Tempo de processamento do passo")
    tool_calls: Optional[List[Dict[str, Any]]] = Field(default=None, description="Chamadas de ferramenta realizadas")


class DebugResponse(BaseModel):
    """Modelo para resposta de debug."""

    id: str = Field(description="ID da conversação")
    debug_log: List[DebugStep] = Field(description="Log detalhado do processamento")
    final_response: Optional[str] = Field(default=None, description="Resposta final gerada")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "conv_debug_123",
            "debug_log": [
                {
                    "node": "agent",
                    "messages": [{"content": "Pensando sobre o problema..."}],
                    "processing_time_ms": 500
                }
            ],
            "final_response": "Resposta completa gerada"
        }
    })


class HealthResponse(BaseModel):
    """Modelo para resposta do health check."""

    status: str = Field(description="Status geral do serviço")
    version: str = Field(description="Versão da API")
    components: Dict[str, Dict[str, Any]] = Field(
        description="Status dos componentes do serviço"
    )
    uptime: Optional[float] = Field(default=None, description="Tempo de atividade em segundos")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "status": "healthy",
            "version": "2.0.0",
            "components": {
                "database": {"status": "connected", "latency_ms": 15},
                "vector_store": {"status": "operational", "doc_count": 1000},
                "agent": {"status": "ready", "tools_count": 2}
            },
            "uptime": 3600.0
        }
    })
