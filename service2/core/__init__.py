# core/__init__.py - Exporta as principais classes e configurações
from .config import settings
from .base import (
    BaseRepository,
    BaseVectorStore,
    BaseService,
    BaseConversationService,
    BaseMessageConverter
)

__all__ = [
    'settings',
    'BaseRepository',
    'BaseVectorStore',
    'BaseService',
    'BaseConversationService',
    'BaseMessageConverter'
]
