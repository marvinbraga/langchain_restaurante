"""
Classes base e interfaces para o Service2.

Este módulo define as abstrações e contratos que serão implementados
por outras camadas da aplicação. Seguimos o Dependency Inversion Principle
para garantir que detalhes de implementação não afetem a arquitetura geral.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, AIMessage


class BaseRepository(ABC):
    """Interface base para todos os repositórios."""

    @abstractmethod
    async def initialize(self) -> None:
        """Inicializa o repositório."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Limpa recursos do repositório."""
        pass


class BaseVectorStore(BaseRepository):
    """Interface para operações com armazenamento vetorial."""

    @abstractmethod
    async def search(self, query: str, limit: int) -> List[Dict[str, Any]]:
        """Busca documentos similares baseado em uma consulta."""
        pass

    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """Adiciona documentos ao armazenamento vetorial."""
        pass


class BaseService(ABC):
    """Interface base para serviços."""

    @abstractmethod
    async def process(self, *args, **kwargs) -> Any:
        """Processa uma requisição."""
        pass


class BaseConversationService(BaseService):
    """Interface para serviços de conversação."""

    @abstractmethod
    async def process_conversation(
            self,
            conversation_id: str,
            messages: List[BaseMessage]
    ) -> AIMessage:
        """Processa uma conversação e retorna uma resposta."""
        pass


class BaseMessageConverter(ABC):
    """Interface para conversão de mensagens."""

    @abstractmethod
    def to_langchain_messages(self, messages: List[Dict]) -> List[BaseMessage]:
        """Converte mensagens do formato da API para formato LangChain."""
        pass

    @abstractmethod
    def from_langchain_message(self, message: BaseMessage) -> Dict:
        """Converte mensagem LangChain para formato da API."""
        pass
