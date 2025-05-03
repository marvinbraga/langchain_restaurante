"""
Repositório para operações com vector store.

Este módulo implementa o Repository Pattern para encapsular toda lógica
de acesso ao armazenamento vetorial. Segue o Single Responsibility Principle
e facilita testes unitários por meio de injeção de dependência.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from ..core.base import BaseVectorStore
from ..core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreRepository(BaseVectorStore):
    """Repositório para operações com PGVector."""

    def __init__(self):
        """Inicializa o repositório com configurações necessárias."""
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._store: Optional[PGVector] = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Inicializa os componentes necessários para o repositório."""
        if self._initialized:
            return

        try:
            # Logger detalhado da connection string para debugging
            logger.info(f"Connection string: {settings.database.connection_string}")

            # Verificar se a string não tem espaços ou caracteres especiais
            conn_str = settings.database.connection_string.strip()
            logger.info(f"Connection string após strip: {conn_str}")

            # Inicializa embeddings com configurações
            self._embeddings = OpenAIEmbeddings(
                api_key=settings.openai.api_key,
                model="text-embedding-3-small",
            )

            # Inicializa o store vetorial
            self._store = PGVector(
                embeddings=self._embeddings,
                connection=conn_str,
                collection_name=settings.vector_store.collection_name,
                # engine_args=self._engine_args,
                async_mode=True,
                use_jsonb=True,
            )

            self._initialized = True
            logger.info("VectorStoreRepository inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar VectorStoreRepository: {e}")
            # Adicionar mais informações de debugging
            logger.error(f"Connection string usada: {settings.database.connection_string}")
            logger.error(f"Tipo da connection string: {type(settings.database.connection_string)}")
            logger.error(f"Comprimento da connection string: {len(settings.database.connection_string)}")
            raise

    async def cleanup(self) -> None:
        """Limpa recursos utilizados pelo repositório."""
        # Em PGVector, não há recursos específicos para limpar
        self._store = None
        self._embeddings = None
        self._initialized = False
        logger.info("VectorStoreRepository finalizado")

    async def search(self, query: str, limit: int = None) -> List[Dict[str, Any]]:
        """
        Busca documentos similares baseado em uma consulta.
        
        Args:
            query: Texto da consulta para busca semântica
            limit: Número máximo de resultados (opcional)
            
        Returns:
            Lista de documentos encontrados com seus metadados
        """
        if not self._initialized:
            await self.initialize()

        if limit is None:
            limit = settings.vector_store.search_limit

        try:
            # Busca com similaridade
            results = self._store.similarity_search_with_score(
                query=query,
                k=limit
            )

            # Formata os resultados
            formatted_results = []
            for doc, score in results:
                if score >= settings.vector_store.similarity_threshold:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "similarity_score": score
                    })

            logger.info(f"Busca realizada: {len(formatted_results)} resultados encontrados")
            return formatted_results

        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            raise

    async def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Adiciona documentos ao armazenamento vetorial.
        
        Args:
            documents: Lista de documentos a serem adicionados
        """
        if not self._initialized:
            await self.initialize()

        try:
            texts = [doc.get("content", "") for doc in documents]
            metadatas = [doc.get("metadata", {}) for doc in documents]

            self._store.add_texts(texts=texts, metadatas=metadatas)
            logger.info(f"{len(documents)} documentos adicionados ao vector store")

        except Exception as e:
            logger.error(f"Erro ao adicionar documentos: {e}")
            raise

    @asynccontextmanager
    async def session(self):
        """
        Context manager para gerenciar sessões do repositório.
        
        Este padrão garante que recursos sejam inicializados quando
        necessário e limpos apropriadamente ao final.
        """
        try:
            await self.initialize()
            yield self
        finally:
            # Em operações normais, mantemos a conexão
            # Limpeza é feita durante shutdown da aplicação
            pass


# Singleton do repositório
vector_store_repository = VectorStoreRepository()
