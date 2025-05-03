"""
Fábrica para criar e configurar agentes ReAct.

Este módulo implementa o Factory Pattern para criar agentes ReAct
configurados com as ferramentas apropriadas e lógica de execução.
"""
import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END, START
from langgraph.prebuilt import ToolNode

from service3.core.base import BaseReActAgent
from service3.core.config import settings
from service3.models.schemas import ReActState
from service3.tools import restaurant_search_tool, menu_suggestion_tool

logger = logging.getLogger(__name__)


class ReActAgent(BaseReActAgent):
    """Implementação de um agente ReAct para o restaurante."""

    def __init__(self, graph, config: Dict[str, Any]):
        """
        Inicializa o agente ReAct.
        
        Args:
            graph: Grafo LangGraph compilado
            config: Configurações do agente
        """
        self._graph = graph
        self._config = config

    async def invoke(self, state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoca o agente com um estado e configuração.
        
        Args:
            state: Estado atual para processar
            config: Configuração de execução
            
        Returns:
            Dicionário com o resultado do processamento
        """
        return await self._graph.ainvoke(state, config)

    async def stream(self, state: Dict[str, Any], config: Dict[str, Any]) -> Any:
        """
        Processa em modo streaming para debugging.
        
        Args:
            state: Estado atual para processar
            config: Configuração de execução
            
        Yields:
            Passos intermediários do processamento
        """
        async for step in self._graph.astream(state, config):
            yield step


class ReActAgentFactory:
    """Fábrica para criar agentes ReAct configurados."""

    @staticmethod
    def create_agent(
            tools: Optional[List] = None,
            system_message: Optional[str] = None,
            model_config: Optional[Dict[str, Any]] = None,
            checkpoint_config: Optional[Dict[str, Any]] = None
    ) -> ReActAgent:
        """
        Cria um novo agente ReAct com configurações especificadas.
        
        Args:
            tools: Lista de ferramentas para o agente usar
            system_message: Mensagem do sistema personalizada
            model_config: Configurações do modelo de linguagem
            checkpoint_config: Configurações de persistência
            
        Returns:
            Instância configurada do agente ReAct
        """
        # Define ferramentas padrão se nenhuma for fornecida
        if tools is None:
            tools = [restaurant_search_tool, menu_suggestion_tool]

        # Define mensagem do sistema padrão se nenhuma for fornecida
        if system_message is None:
            system_message = settings.react_agent.system_message

        # Configura modelo de linguagem
        if model_config is None:
            model_config = {
                "model": settings.openai.model,
                "temperature": settings.openai.temperature,
                "api_key": settings.openai.api_key
            }

        llm = ChatOpenAI(**model_config)
        model_with_tools = llm.bind_tools(tools)

        # Cria os nós do grafo
        def call_model(state: ReActState) -> Dict[str, Any]:
            """Nó que chama o modelo para decidir a próxima ação."""
            messages = state["messages"]

            # Adiciona mensagem do sistema se não estiver presente
            if not any(isinstance(msg, SystemMessage) for msg in messages):
                system_msg = SystemMessage(content=system_message)
                messages = [system_msg] + messages

            response = model_with_tools.invoke(messages)
            return {"messages": [response]}

        def should_continue(state: ReActState) -> str:
            """Determina se deve continuar com chamadas de ferramenta ou finalizar."""
            last_message = state["messages"][-1]

            # Se a última mensagem tem tool calls, continua
            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "tools"
            # Caso contrário, finaliza a conversação
            return END

        # Cria o nó de ferramentas
        tool_node = ToolNode(tools)

        # Constrói o grafo
        workflow = StateGraph(ReActState)

        # Adiciona nós
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)

        # Define a estrutura do grafo
        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END,
            }
        )
        workflow.add_edge("tools", "agent")

        # Configura persistência
        if checkpoint_config is None:
            checkpoint_config = {"checkpointer": MemorySaver()}

        # Compila o grafo
        compiled_graph = workflow.compile(**checkpoint_config)

        # Cria configuração do agente
        agent_config = {
            "tools": tools,
            "system_message": system_message,
            "model_config": model_config,
            "checkpoint_config": checkpoint_config,
            "verbose": settings.react_agent.verbose
        }

        return ReActAgent(compiled_graph, agent_config)

    @staticmethod
    def create_debug_agent(**kwargs) -> ReActAgent:
        """
        Cria um agente ReAct configurado para debugging com logs verbosos.
        
        Args:
            **kwargs: Argumentos adicionais para criar_agent
            
        Returns:
            Agente configurado para debug
        """
        # Configura para modo verbose
        debug_config = kwargs.get('model_config', {}).copy()
        debug_config['temperature'] = 0.1  # Mais determinístico para debug

        kwargs['model_config'] = debug_config
        return ReActAgentFactory.create_agent(**kwargs)


# Factory global
react_agent_factory = ReActAgentFactory()


# Função de conveniência para criar agente padrão
def create_default_agent() -> ReActAgent:
    """
    Cria um agente ReAct com configurações padrão.
    
    Returns:
        Agente ReAct configurado com settings padrão
    """
    return react_agent_factory.create_agent()
