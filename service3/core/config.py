"""
Configurações centralizadas para o Service3 com suporte ao agente ReAct.

Este módulo contém todas as configurações necessárias para o funcionamento
do Service3, incluindo configurações específicas para o agente ReAct.
"""
import os
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings

load_dotenv(find_dotenv())


class DatabaseSettings(BaseSettings):
    """Configurações específicas do banco de dados PostgreSQL."""

    host: str = os.environ["POSTGRES_HOST"]
    port: int = os.environ.get("POSTGRES_PORT", 5432)
    user: str = os.environ["POSTGRES_USER"]
    password: str = os.environ["POSTGRES_PASSWORD"]
    database: str = os.environ["POSTGRES_DATABASE"]

    @property
    def connection_string(self) -> str:
        """Gera a string de conexão completa para o PostgreSQL."""
        return f"postgresql+psycopg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    class Config:
        env_prefix = "POSTGRES_"


class OpenAISettings(BaseSettings):
    """Configurações relacionadas à API OpenAI."""

    api_key: str = os.getenv("OPENAI_API_KEY", "")
    model: str = "gpt-4o-mini"
    temperature: float = 0.7
    max_tokens: Optional[int] = None

    class Config:
        env_prefix = "OPENAI_"


class VectorStoreSettings(BaseSettings):
    """Configurações para o armazenamento vetorial."""

    collection_name: str = "vectordb"
    search_limit: int = 3
    similarity_threshold: float = 0.7
    embedding_model: str = "text-embedding-3-small"

    class Config:
        env_prefix = "VECTOR_"


class ReActAgentSettings(BaseSettings):
    """Configurações específicas para o agente ReAct."""

    max_iterations: int = 10
    verbose: bool = False
    system_message: str = """You are a helpful restaurant FAQ assistant. You have access to a database of restaurant 
information through the search_restaurant_information tool and can provide menu suggestions with 
the provide_menu_suggestions tool. 

Use the ReAct pattern: think about what information you need, use appropriate tools to gather 
information, and then provide a comprehensive answer to the customer.

Always be friendly, helpful, and maintain a professional restaurant service tone."""

    class Config:
        env_prefix = "REACT_AGENT_"


class ApplicationSettings(BaseSettings):
    """Configurações gerais da aplicação."""

    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    version: str = "2.0.0"

    # Configurações de sub-componentes
    database: DatabaseSettings = DatabaseSettings()
    openai: OpenAISettings = OpenAISettings()
    vector_store: VectorStoreSettings = VectorStoreSettings()
    react_agent: ReActAgentSettings = ReActAgentSettings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Permitir campos extras para evitar erros de validação
        extra = "allow"


# Singleton da configuração
settings = ApplicationSettings()
