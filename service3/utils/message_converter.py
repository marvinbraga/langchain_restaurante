"""
Conversor de mensagens entre formatos.

Este módulo implementa a conversão entre diferentes formatos de mensagens,
abstraindo os detalhes de transformação de dados para o agente ReAct.
"""
from typing import List, Dict, Any, Optional

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

from service3.core.base import BaseMessageConverter
from service3.models.schemas import MessageRole


class MessageConverter(BaseMessageConverter):
    """Conversor de mensagens entre formato API e LangChain."""

    def __init__(self):
        """Inicializa os mapeamentos de tipos de mensagem."""
        self._api_to_langchain = {
            MessageRole.USER: HumanMessage,
            MessageRole.ASSISTANT: AIMessage,
            MessageRole.SYSTEM: SystemMessage
        }

        self._langchain_to_api = {
            "human": MessageRole.USER,
            "ai": MessageRole.ASSISTANT,
            "system": MessageRole.SYSTEM
        }

    def to_langchain_messages(self, messages: List[Dict[str, str]]) -> List[BaseMessage]:
        """
        Converte mensagens do formato da API para formato LangChain.
        
        Args:
            messages: Lista de mensagens no formato API (dicionários)
            
        Returns:
            Lista de objetos BaseMessage do LangChain
            
        Raises:
            ValueError: Se um tipo de mensagem inválido for encontrado
        """
        langchain_messages = []

        for msg in messages:
            try:
                role = MessageRole(msg.get("role", ""))
                content = msg.get("content", "")

                if role not in self._api_to_langchain:
                    raise ValueError(f"Tipo de mensagem inválido: {role}")

                message_class = self._api_to_langchain[role]
                langchain_message = message_class(content=content)
                langchain_messages.append(langchain_message)

            except ValueError as e:
                # Log o erro mas continua com outras mensagens
                import logging
                logging.getLogger(__name__).error(f"Erro ao converter mensagem: {e}")
                continue

        return langchain_messages

    def from_langchain_message(self, message: BaseMessage) -> Dict[str, str]:
        """
        Converte uma mensagem LangChain para formato da API.
        
        Args:
            message: Objeto BaseMessage do LangChain
            
        Returns:
            Dicionário com formato da API
            
        Raises:
            ValueError: Se o tipo de mensagem não for reconhecido
        """
        message_type = message.type

        if message_type not in self._langchain_to_api:
            raise ValueError(f"Tipo de mensagem LangChain não reconhecido: {message_type}")

        return {
            "role": self._langchain_to_api[message_type].value,
            "content": message.content if hasattr(message, 'content') else str(message)
        }

    def to_conversation_dict(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        Converte uma lista de mensagens LangChain para o formato Conversation da API.
        
        Args:
            messages: Lista de mensagens LangChain
            
        Returns:
            Dicionário no formato Conversation
        """
        converted_messages = []
        for msg in messages:
            try:
                converted_msg = self.from_langchain_message(msg)
                converted_messages.append(converted_msg)
            except ValueError as e:
                # Ignora mensagens que não podem ser convertidas
                import logging
                logging.getLogger(__name__).warning(f"Mensagem ignorada durante conversão: {e}")
                continue

        return {"conversation": converted_messages}

    def to_langchain_conversation(self, conversation: Dict[str, Any]) -> List[BaseMessage]:
        """
        Converte um dicionário Conversation para lista de mensagens LangChain.
        
        Args:
            conversation: Dicionário com formato Conversation
            
        Returns:
            Lista de mensagens LangChain
        """
        messages = conversation.get("conversation", [])
        return self.to_langchain_messages(messages)

    def extract_user_messages(self, messages: List[BaseMessage]) -> List[str]:
        """
        Extrai apenas o conteúdo das mensagens do usuário.
        
        Args:
            messages: Lista de mensagens LangChain
            
        Returns:
            Lista de strings com o conteúdo das mensagens do usuário
        """
        user_contents = []

        for msg in messages:
            if msg.type == "human":
                if hasattr(msg, 'content') and msg.content:
                    user_contents.append(msg.content)

        return user_contents

    def extract_last_user_message(self, messages: List[BaseMessage]) -> Optional[str]:
        """
        Extrai a última mensagem do usuário.
        
        Args:
            messages: Lista de mensagens LangChain
            
        Returns:
            Conteúdo da última mensagem do usuário ou None
        """
        for msg in reversed(messages):
            if msg.type == "human" and hasattr(msg, 'content') and msg.content:
                return msg.content

        return None

    def count_messages_by_role(self, messages: List[BaseMessage]) -> Dict[str, int]:
        """
        Conta mensagens por papel/tipo.
        
        Args:
            messages: Lista de mensagens LangChain
            
        Returns:
            Dicionário com contagem por tipo
        """
        counts = {
            "human": 0,
            "ai": 0,
            "system": 0,
            "other": 0
        }

        for msg in messages:
            msg_type = getattr(msg, 'type', 'other')
            if msg_type in counts:
                counts[msg_type] += 1
            else:
                counts["other"] += 1

        return counts


# Singleton do conversor
message_converter = MessageConverter()
