# core/__init__.py - Exporta classes e configurações principais do core
from service3.core.base import (
    BaseRepository,
    BaseVectorStore,
    BaseAgentService,
    BaseReActAgent,
    BaseTool,
    BaseMessageConverter
)
from service3.core.config import settings

__all__ = [
    'settings',
    'BaseRepository',
    'BaseVectorStore',
    'BaseAgentService',
    'BaseReActAgent',
    'BaseTool',
    'BaseMessageConverter'
]
