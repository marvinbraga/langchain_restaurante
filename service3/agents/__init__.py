# agents/__init__.py - Exporta agentes e fábricas
from service3.agents.react_factory import (
    ReActAgent,
    ReActAgentFactory,
    react_agent_factory,
    create_default_agent
)

__all__ = [
    'ReActAgent',
    'ReActAgentFactory',
    'react_agent_factory',
    'create_default_agent'
]
