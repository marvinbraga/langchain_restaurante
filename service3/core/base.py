"""
Classes base e interfaces para o Service3.

Este módulo define as abstrações e contratos que serão implementados
por outras camadas da aplicação. Inclui interfaces específicas para
o sistema de agentes e tools.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage


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


class BaseAgentService(ABC):
    """Interface base para serviços de agentes."""

    @abstractmethod
    async def process(self, conversation_id: str, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Processa uma conversação usando o agente."""
        pass

    @abstractmethod
    async def debug(self, conversation_id: str, messages: List[BaseMessage]) -> Dict[str, Any]:
        """Processa uma conversação em modo debug para ver o reasoning."""
        pass


class BaseReActAgent(ABC):
    """Interface para agentes ReAct."""

    @abstractmethod
    async def invoke(self, state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Invoca o agente com um estado e configuração."""
        pass

    @abstractmethod
    async def stream(self, state: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """Processa em modo streaming para debugging."""
        pass


class BaseTool(ABC):
    """Interface base para ferramentas do agente."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Nome da ferramenta."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Descrição da ferramenta."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Executa a ferramenta com os parâmetros fornecidos."""
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
