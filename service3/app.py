"""
FastAPI entry point para o Service3.

Este módulo configura e inicializa a aplicação FastAPI com o agente ReAct,
definindo rotas e gerenciando o ciclo de vida da aplicação.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from service3.core.config import settings
from service3.models.schemas import Conversation, AgentResponse, DebugResponse, HealthResponse
from service3.repositories import vector_store_repository
from service3.services import react_agent_service
from service3.utils.message_converter import message_converter

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Gerenciador de contexto para ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    
    Inicializa recursos necessários no startup e limpa recursos no shutdown.
    """
    try:
        # Startup - Inicializa recursos
        logger.info(f"Iniciando o Service3 v{settings.version}...")

        # Inicializa vector store
        await vector_store_repository.initialize()

        # Verifica agente configurado
        logger.info(
            f"Agente ReAct configurado com {len(react_agent_service.agent_config.get('tools', []))} ferramentas")

        logger.info("Service3 iniciado com sucesso")

        yield

    finally:
        # Shutdown - Limpa recursos
        logger.info("Finalizando o Service3...")
        await vector_store_repository.cleanup()
        logger.info("Service3 finalizado")


# Cria a aplicação FastAPI
app = FastAPI(
    title="Restaurant FAQ Service with ReAct Agent",
    description="Serviço de FAQ para restaurante usando agente ReAct",
    version=settings.version,
    lifespan=lifespan
)

# Configura CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post(
    "/service3/{conversation_id}",
    response_model=AgentResponse,
    summary="Processa uma conversação com o agente ReAct",
    description="Processa uma conversa usando o agente ReAct que pode buscar informações e sugerir menu."
)
async def process_conversation(
        conversation_id: str,
        conversation: Conversation,
        background_tasks: BackgroundTasks
) -> AgentResponse:
    """
    Processa uma conversação usando o agente ReAct.
    
    Args:
        conversation_id: ID único da conversação
        conversation: Dados da conversa
        background_tasks: Tarefas em background
        
    Returns:
        Resposta processada com metadados
    """
    try:
        # Converte mensagens para formato LangChain
        messages = message_converter.to_langchain_conversation({"conversation": conversation.conversation})

        # Processa com o agente ReAct
        result = await react_agent_service.process(conversation_id, messages)

        # Adiciona log em background
        background_tasks.add_task(
            log_conversation_metrics,
            conversation_id,
            result.get("metadata", {})
        )

        return AgentResponse(**result)

    except ValueError as e:
        logger.error(f"Erro de validação na conversação {conversation_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Erro ao processar conversação {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar conversação")


@app.post(
    "/service3/{conversation_id}/debug",
    response_model=DebugResponse,
    summary="Debug do processamento do agente ReAct",
    description="Mostra passos detalhados do reasoning do agente durante o processamento."
)
async def debug_conversation(
        conversation_id: str,
        conversation: Conversation
) -> DebugResponse:
    """
    Executa o agente ReAct em modo debug.
    
    Args:
        conversation_id: ID único da conversação
        conversation: Dados da conversa
        
    Returns:
        Log detalhado do processamento
    """
    try:
        # Converte mensagens para formato LangChain
        messages = message_converter.to_langchain_conversation({"conversation": conversation.conversation})

        # Processa em modo debug
        result = await react_agent_service.debug(conversation_id, messages)

        return DebugResponse(**result)

    except Exception as e:
        logger.error(f"Erro no debug da conversação {conversation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro no modo debug: {str(e)}")


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica a saúde do serviço",
    description="Retorna o status do serviço e seus componentes."
)
async def health_check() -> HealthResponse:
    """
    Verifica a saúde do serviço e seus componentes.
    
    Returns:
        Status do serviço e seus componentes
    """
    try:
        # Verifica vector store
        vector_store_status = await vector_store_repository.health_check()

        # Verifica agente
        agent_stats = react_agent_service.get_stats()
        agent_config = react_agent_service.agent_config

        return HealthResponse(
            status="healthy" if vector_store_status.get("status") == "operational" else "unhealthy",
            version=settings.version,
            components={
                "database": {
                    "status": "connected",
                    "connection_string": settings.database.connection_string.split("@")[-1]
                },
                "vector_store": vector_store_status,
                "agent": {
                    "status": "ready",
                    "tools_count": len(agent_config.get("tools", [])),
                    "model": settings.openai.model,
                    "stats": agent_stats
                }
            }
        )

    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return HealthResponse(
            status="unhealthy",
            version=settings.version,
            components={
                "error": {"status": "error", "message": str(e)}
            }
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Handler global para exceções não tratadas.
    
    Garante que todas as exceções sejam apropriadamente logadas
    e retornem uma resposta adequada.
    """
    logger.error(f"Erro não tratado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"}
    )


# Funções auxiliares para tarefas em background
async def log_conversation_metrics(conversation_id: str, metadata: Dict[str, Any]) -> None:
    """
    Registra métricas da conversação para análise posterior.
    
    Args:
        conversation_id: ID da conversação
        metadata: Metadados da resposta
    """
    try:
        # Aqui você poderia enviar métricas para um sistema de monitoramento
        logger.info(f"Métricas da conversação {conversation_id}: {metadata}")
    except Exception as e:
        logger.error(f"Erro ao registrar métricas: {e}")


# Permite execução direta para desenvolvimento
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=80,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )
