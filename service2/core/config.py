"""
Configurações centralizadas da aplicação.

Este módulo contém todas as configurações necessárias para o funcionamento
do Service2, seguindo o padrão Settings Pattern para gerenciamento de 
configurações de forma limpa e organizada.
"""
import os

from dotenv import load_dotenv, find_dotenv
from pydantic_settings import BaseSettings

load_dotenv(find_dotenv())


class DatabaseSettings(BaseSettings):
    """Configurações específicas do banco de dados PostgreSQL."""

    host: str = os.environ.get("POSTGRES_HOST", "postgres")
    port: int = int(os.environ.get("POSTGRES_PORT", "5432"))
    user: str = os.environ.get("POSTGRES_USER", "admin")
    password: str = os.environ.get("POSTGRES_PASSWORD", "admin")
    database: str = os.environ.get("POSTGRES_DB", "vectordb")

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
    temperature: float = 0.0

    class Config:
        env_prefix = "OPENAI_"


class VectorStoreSettings(BaseSettings):
    """Configurações para o armazenamento vetorial."""

    collection_name: str = "vectordb"
    search_limit: int = 3
    similarity_threshold: float = 0.7

    class Config:
        env_prefix = "VECTOR_"


class Service3Settings(BaseSettings):
    """Configurações para comunicação com o Service3."""

    host: str = os.getenv("SERVICE3_HOST", "service3")
    port: int = int(os.getenv("SERVICE3_PORT", "80"))
    timeout: int = 30

    @property
    def base_url(self) -> str:
        """Retorna a URL base do Service3."""
        return f"http://{self.host}:{self.port}"


class ApplicationSettings(BaseSettings):
    """Configurações gerais da aplicação."""

    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Configurações de sub-componentes
    database: DatabaseSettings = DatabaseSettings()
    openai: OpenAISettings = OpenAISettings()
    vector_store: VectorStoreSettings = VectorStoreSettings()
    service3: Service3Settings = Service3Settings()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        # Permitir campos extras (fix rápido)
        extra = "allow"


# Singleton da configuração
settings = ApplicationSettings()
