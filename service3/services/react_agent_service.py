"""
Serviço do agente ReAct para processamento de conversações.

Este módulo implementa a lógica de negócios para processamento de
conversações usando o agente ReAct, incluindo modo de debug.
"""
import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from langchain_core.messages import BaseMessage

from service3.agents import ReActAgent, create_default_agent
from service3.core.base import BaseAgentService
from service3.core.config import settings
from service3.models.schemas import DebugStep

logger = logging.getLogger(__name__)


class ReActAgentService(BaseAgentService):
    """Serviço responsável pelo processamento de conversações com agente ReAct."""

    def __init__(self, agent: Optional[ReActAgent] = None):
        """
        Inicializa o serviço com um agente ReAct.
        
        Args:
            agent: Instância do agente ReAct (opcional)
        """
        self._agent = agent or create_default_agent()
        self._processing_stats = {
            "total_conversations": 0,
            "total_processing_time": 0.0,
            "average_processing_time": 0.0
        }

    async def process(
            self,
            conversation_id: str,
            messages: List[BaseMessage]
    ) -> Dict[str, Any]:
        """
        Processa uma conversação usando o agente ReAct.
        
        Args:
            conversation_id: ID único da conversação
            messages: Lista de mensagens no formato LangChain
            
        Returns:
            Dicionário com resposta e metadados
        """
        start_time = time.time()

        try:
            # Configura thread persistence
            config = {"configurable": {"thread_id": conversation_id}}

            # Prepara estado inicial
            state = {"messages": messages}

            # Processa com o agente
            result = await self._agent.invoke(state, config)

            # Extrai resposta final
            final_messages = result.get("messages", [])
            reply = self._extract_final_reply(final_messages)

            # Calcula tempo de processamento
            processing_time = (time.time() - start_time) * 1000  # em ms

            # Atualiza estatísticas
            self._update_stats(processing_time)

            # Prepara resposta
            return {
                "id": conversation_id,
                "reply": reply,
                "metadata": {
                    "processing_time_ms": round(processing_time, 2),
                    "model": settings.openai.model,
                    "tool_count": len(self._agent._config.get("tools", [])),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Erro ao processar conversação {conversation_id}: {e}")
            raise

    async def debug(
            self,
            conversation_id: str,
            messages: List[BaseMessage]
    ) -> Dict[str, Any]:
        """
        Processa uma conversação em modo debug para análise do reasoning.
        
        Args:
            conversation_id: ID único da conversação
            messages: Lista de mensagens no formato LangChain
            
        Returns:
            Dicionário com log detalhado do processamento
        """
        try:
            # Configura thread persistence
            config = {"configurable": {"thread_id": conversation_id}}

            # Prepara estado inicial
            state = {"messages": messages}

            # Stream para debug
            debug_log = []
            final_response = None

            async for step in self._agent.stream(state, config):
                for node, node_state in step.items():
                    # Extrai informações do passo
                    step_info = self._process_debug_step(node, node_state)
                    debug_log.append(step_info)

                    # Captura resposta final se for o último passo
                    if node == "agent" and not step_info.tool_calls:
                        final_response = self._extract_final_reply(
                            node_state.get("messages", [])
                        )

            return {
                "id": conversation_id,
                "debug_log": debug_log,
                "final_response": final_response or "Nenhuma resposta gerada",
                "metadata": {
                    "total_steps": len(debug_log),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

        except Exception as e:
            logger.error(f"Erro no debug da conversação {conversation_id}: {e}")
            raise

    def _extract_final_reply(self, messages: List[BaseMessage]) -> str:
        """
        Extrai a resposta final das mensagens.
        
        Args:
            messages: Lista de mensagens
            
        Returns:
            Texto da resposta final
        """
        if not messages:
            return "Nenhuma resposta gerada. Por favor, tente novamente."

        # Pega a última mensagem
        last_message = messages[-1]

        # Verifica se é uma mensagem do assistente
        if hasattr(last_message, 'content'):
            content = last_message.content
            if content and not hasattr(last_message, 'tool_calls'):
                return content

        return "Não foi possível processar sua solicitação. Por favor, tente novamente."

    def _process_debug_step(self, node: str, state: Dict[str, Any]) -> DebugStep:
        """
        Processa um passo de debug e extrai informações relevantes.
        
        Args:
            node: Nome do nó processado
            state: Estado atual do nó
            
        Returns:
            DebugStep com informações formatadas
        """
        messages = state.get("messages", [])

        # Extrai tool calls se houver
        tool_calls = None
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, 'tool_calls') and last_msg.tool_calls:
                tool_calls = [
                    {
                        "name": call.get("name"),
                        "args": call.get("args", {})
                    }
                    for call in last_msg.tool_calls
                ]

        # Formata mensagens para debug
        debug_messages = []
        for msg in messages:
            if hasattr(msg, 'content'):
                debug_messages.append({
                    "type": getattr(msg, 'type', 'unknown'),
                    "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                })

        return DebugStep(
            node=node,
            messages=debug_messages,
            tool_calls=tool_calls
        )

    def _update_stats(self, processing_time: float) -> None:
        """
        Atualiza estatísticas de processamento.
        
        Args:
            processing_time: Tempo de processamento em ms
        """
        self._processing_stats["total_conversations"] += 1
        self._processing_stats["total_processing_time"] += processing_time
        self._processing_stats["average_processing_time"] = (
                self._processing_stats["total_processing_time"] /
                self._processing_stats["total_conversations"]
        )

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de processamento."""
        return self._processing_stats.copy()

    @property
    def agent_config(self) -> Dict[str, Any]:
        """Retorna configuração do agente."""
        return self._agent._config if hasattr(self._agent, '_config') else {}


# Singleton do serviço
react_agent_service = ReActAgentService()
