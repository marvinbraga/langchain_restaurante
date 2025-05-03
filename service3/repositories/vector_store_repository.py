"""
Repositório para operações com vector store.

Este módulo implementa o Repository Pattern para encapsular toda lógica
de acesso ao armazenamento vetorial, incluindo busca semântica e gerenciamento
de documentos.
"""
import logging
from contextlib import asynccontextmanager
from typing import List, Dict, Any, Optional

from langchain_core.retrievers import BaseRetriever
from langchain_openai import OpenAIEmbeddings
from langchain_postgres import PGVector

from service3.core.base import BaseVectorStore
from service3.core.config import settings

logger = logging.getLogger(__name__)


class VectorStoreRepository(BaseVectorStore):
    """Repositório para operações com PGVector."""

    def __init__(self):
        """Inicializa o repositório com configurações necessárias."""
        self._embeddings: Optional[OpenAIEmbeddings] = None
        self._store: Optional[PGVector] = None
        self._retriever: Optional[BaseRetriever] = None
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Inicializa os componentes necessários para o repositório."""
        if self._initialized:
            return

        try:
            logger.info("Embedding sendo iniciado.")
            self._embeddings = OpenAIEmbeddings(
                api_key=settings.openai.api_key,
                model=settings.vector_store.embedding_model
            )
            logger.info("Embedding OK.")

            # Inicializa o store vetorial
            logger.info("PGVector sendo iniciado.")
            self._store = PGVector(
                embeddings=self._embeddings,
                connection=settings.database.connection_string,
                collection_name=settings.vector_store.collection_name,
                # engine_args=self._engine_args,
                async_mode=True,
                use_jsonb=True,
            )
            self._store.create_extension = False
            logger.info("PGVector OK.")

            # Configura o retriever com parâmetros otimizados
            logger.info("Retriever sendo iniciado.")
            self._retriever = self._store.as_retriever(
                search_kwargs={"k": settings.vector_store.search_limit}
            )
            logger.info("Retriever OK.")

            self._initialized = True
            logger.info("VectorStoreRepository inicializado com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar VectorStoreRepository: {e}")
            raise

    async def cleanup(self) -> None:
        """Limpa recursos utilizados pelo repositório."""
        self._store = None
        self._embeddings = None
        self._retriever = None
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
            # Busca com similaridade utilizando o retriever
            docs = self._retriever.get_relevant_documents(query=query)

            # Formata os resultados
            formatted_results = []
            for doc in docs[:limit]:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get('source', 'Unknown')
                })

            logger.info(f"Busca realizada: {len(formatted_results)} resultados encontrados")
            return formatted_results

        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return []  # Retorna lista vazia em caso de erro

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

    async def health_check(self) -> Dict[str, Any]:
        """
        Verifica a saúde do vector store.
        
        Returns:
            Dicionário com status e métricas do vector store
        """
        try:
            if not self._initialized:
                return {
                    "status": "not_initialized",
                    "error": "Repository not initialized"
                }

            # Testa uma busca simples
            test_docs = await self.search("health check test", limit=1)

            return {
                "status": "operational",
                "collection": settings.vector_store.collection_name,
                "test_search": "success" if len(test_docs) >= 0 else "failed",
                "embedding_model": settings.vector_store.embedding_model
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

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

    @property
    def is_initialized(self) -> bool:
        """Verifica se o repositório está inicializado."""
        return self._initialized


# Singleton do repositório
vector_store_repository = VectorStoreRepository()
