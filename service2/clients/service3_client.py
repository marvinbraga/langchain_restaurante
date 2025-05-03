"""
Cliente HTTP para comunicação com o Service3.

Este módulo implementa a comunicação assíncrona com o Service3,
seguindo o pattern HTTP Client para integração de serviços.
"""
import logging
from typing import Dict, Any

import httpx

from service2.core.config import settings

logger = logging.getLogger(__name__)


class Service3Client:
    """Cliente para comunicação com o Service3."""

    def __init__(self, base_url: str, timeout: int = 30):
        """
        Inicializa o cliente HTTP.
        
        Args:
            base_url: URL base do Service3
            timeout: Timeout para requisições em segundos
        """
        self._base_url = base_url
        self._timeout = timeout
        self._client = None

    async def initialize(self) -> None:
        """Inicializa o cliente HTTP."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
            )
            logger.info(f"Cliente HTTP inicializado para {self._base_url}")

    async def cleanup(self) -> None:
        """Fecha o cliente HTTP."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("Cliente HTTP fechado")

    async def process_conversation(
        self,
        conversation_id: str,
        conversation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Envia uma conversação para o Service3 processar.
        
        Args:
            conversation_id: ID da conversação
            conversation_data: Dados da conversação
            
        Returns:
            Resposta do Service3
            
        Raises:
            httpx.HTTPError: Em caso de erro na requisição
        """
        if not self._client:
            await self.initialize()

        endpoint = f"/service3/{conversation_id}"
        
        try:
            logger.info(f"Enviando requisição para {endpoint}")
            response = await self._client.post(endpoint, json=conversation_data)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Resposta recebida com status {response.status_code}")
            
            return result

        except httpx.HTTPStatusError as e:
            logger.error(f"Erro HTTP {e.response.status_code}: {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Erro de requisição: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro inesperado: {e}")
            raise


def create_service3_client() -> Service3Client:
    """
    Factory method para criar instância do cliente Service3.
    
    Returns:
        Instância configurada do cliente
    """
    return Service3Client(
        base_url=settings.service3.base_url,
        timeout=settings.service3.timeout
    )
