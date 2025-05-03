"""
FastAPI entry point para o Service2.

Este módulo configura e inicializa a aplicação FastAPI, definindo rotas
e gerenciando o ciclo de vida da aplicação. Segue o Facade Pattern
para fornecer uma interface simples aos componentes da aplicação.
"""
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

import httpx
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from service2.core.config import settings
from service2.models.schemas import Conversation, ConversationResponse, HealthResponse
from service2.repositories import vector_store_repository
from service2.services.conversation_service import create_conversation_service
from service2.clients import create_service3_client

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Gerenciador de contexto para ciclo de vida da aplicação
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gerencia o ciclo de vida da aplicação FastAPI.
    
    Inicializa recursos necessários no startup e limpa recursos no shutdown,
    implementando o Resource Management Pattern.
    """
    try:
        # Startup - Inicializa recursos
        logger.info("Iniciando o Service2...")
        await vector_store_repository.initialize()
        
        # Inicializa cliente do Service3
        await service3_client.initialize()
        
        logger.info("Service2 iniciado com sucesso")

        yield

    finally:
        # Shutdown - Limpa recursos
        logger.info("Finalizando o Service2...")
        await vector_store_repository.cleanup()
        await service3_client.cleanup()
        logger.info("Service2 finalizado")


# Cria a aplicação FastAPI
app = FastAPI(
    title="Restaurant FAQ Service",
    description="Serviço de FAQ para restaurante usando IA",
    version="2.0.0",
    lifespan=lifespan
)

# Configura CORS com política permissiva para desenvolvimento
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cria instância do serviço de conversação
conversation_service = create_conversation_service(vector_store_repository)

# Cria cliente para comunicação com Service3
service3_client = create_service3_client()


@app.post(
    "/conversation/{conversation_id}",
    response_model=ConversationResponse,
    summary="Processa uma conversação com o agente ReAct",
    description="Processa uma conversação e retorna uma resposta do agente ReAct."
)
async def process_conversation(
        conversation_id: str,
        conversation: Conversation,
        background_tasks: BackgroundTasks
) -> ConversationResponse:
    """
    Processa uma conversação completa.
    
    Args:
        conversation_id: ID único da conversação
        conversation: Dados da conversa
        background_tasks: Tarefas em background
        
    Returns:
        Resposta processada com metadados
    """
    try:
        # Envia a requisição para o Service3
        response = await service3_client.process_conversation(
            conversation_id=conversation_id,
            conversation_data=conversation.dict()
        )

        # Adiciona tarefa de logging em background
        background_tasks.add_task(
            log_conversation_metrics,
            conversation_id,
            response.get("metadata", {})
        )

        return ConversationResponse(**response)

    except httpx.HTTPStatusError as e:
        logger.error(f"Erro: {e}")
        logger.error(f"Erro HTTP ao comunicar com Service3: {e.response.status_code}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Erro ao comunicar com Service3: {e.response.text}"
        )
    except httpx.RequestError as e:
        logger.error(f"Erro de rede ao comunicar com Service3: {e}")
        raise HTTPException(
            status_code=503,
            detail="Service3 indisponível"
        )
    except ValueError as e:
        logger.error(f"Erro de validação na conversação {conversation_id}: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Erro ao processar conversação {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar conversação")


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
        # Verifica conexão com o vector store
        test_search = await vector_store_repository.search("test", limit=1)
        vector_store_status = {
            "status": "operational",
            "response_time_ms": 0  # Adicionar timing se necessário
        }

        return HealthResponse(
            status="healthy",
            components={
                "database": {
                    "status": "connected",
                    "connection_string": settings.database.connection_string.split("@")[-1]
                },
                "vector_store": vector_store_status,
                "openai": {
                    "status": "configured",
                    "model": settings.openai.model
                },
                "service3": {
                    "status": "available",
                    "base_url": settings.service3.base_url
                }
            }
        )

    except Exception as e:
        logger.error(f"Health check falhou: {e}")
        return HealthResponse(
            status="unhealthy",
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
        content={"detail": f"Erro interno do servidor | {exc}"}
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
        log_level="info"
    )
