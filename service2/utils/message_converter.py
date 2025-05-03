"""
Conversor de mensagens entre formatos.

Este módulo implementa a conversão entre diferentes formatos de mensagens,
abstraindo os detalhes de transformação de dados. Segue o Adapter Pattern
para facilitar a integração entre diferentes representações de mensagens.
"""
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

from ..core.base import BaseMessageConverter
from ..models.schemas import MessageRole


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
            "content": message.content
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
            except ValueError:
                # Ignora mensagens que não podem ser convertidas
                continue

        return {"conversation": converted_messages}

    def extract_user_content(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Extrai apenas o conteúdo das mensagens do usuário.
        
        Args:
            messages: Lista de mensagens no formato API
            
        Returns:
            Lista de strings com o conteúdo das mensagens do usuário
        """
        user_contents = []

        for msg in messages:
            if msg.get("role") == MessageRole.USER:
                content = msg.get("content", "")
                if content:
                    user_contents.append(content)

        return user_contents

    def extract_assistant_content(self, messages: List[Dict[str, str]]) -> List[str]:
        """
        Extrai apenas o conteúdo das mensagens do assistente.
        
        Args:
            messages: Lista de mensagens no formato API
            
        Returns:
            Lista de strings com o conteúdo das mensagens do assistente
        """
        assistant_contents = []

        for msg in messages:
            if msg.get("role") == MessageRole.ASSISTANT:
                content = msg.get("content", "")
                if content:
                    assistant_contents.append(content)

        return assistant_contents


# Singleton do conversor
message_converter = MessageConverter()
