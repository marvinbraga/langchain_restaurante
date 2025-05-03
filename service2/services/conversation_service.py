"""
Serviço de processamento de conversações.

Este módulo implementa a lógica de negócios para processamento de conversações,
seguindo o Service Pattern. Orquestra o uso de repositórios e utilidades para
implementar as regras de negócio específicas do domínio.
"""
import logging
from datetime import datetime
from typing import List, Dict, Any

from langchain_core.messages import BaseMessage
from langchain_core.prompts import PromptTemplate, SystemMessagePromptTemplate
from langchain_openai import ChatOpenAI

from service2.core.base import BaseConversationService
from service2.core.config import settings
from service2.repositories import VectorStoreRepository
from service2.utils.message_converter import message_converter

logger = logging.getLogger(__name__)


class ConversationService(BaseConversationService):
    """Serviço responsável pelo processamento de conversações."""

    def __init__(self, vector_store: VectorStoreRepository):
        """
        Inicializa o serviço com dependências necessárias.
        
        Args:
            vector_store: Repositório de armazenamento vetorial
        """
        self._vector_store = vector_store
        self._chat_model = None
        self._prompt_template = None
        self._initialized = False

    async def _initialize(self) -> None:
        """Inicializa os componentes necessários lazy loading."""
        if self._initialized:
            return

        # Inicializa o modelo de chat
        self._chat_model = ChatOpenAI(
            model=settings.openai.model,
            temperature=settings.openai.temperature,
            api_key=settings.openai.api_key
        )

        # Define o template do prompt
        prompt_template = """
        Como um FAQ Bot para nosso restaurante, você tem as seguintes informações:

        {context}

        Por favor, forneça a resposta mais adequada para a pergunta do usuário.
        Seja amigável, profissional e use apenas as informações fornecidas.
        
        Resposta:"""

        self._prompt_template = PromptTemplate(
            template=prompt_template,
            input_variables=["context"]
        )

        self._initialized = True
        logger.info("ConversationService inicializado")

    async def process(self, *args, **kwargs) -> Any:
        """
        Método genérico para processar diferentes tipos de inputs.
        
        Este método serve como uma interface flexível que pode lidar com diferentes
        formatos de entrada. Ele delega para os métodos específicos baseado nos tipos
        dos argumentos recebidos.
        
        Args:
            *args: Argumentos posicionais (conversation_id, messages, etc.)
            **kwargs: Argumentos nomeados que podem incluir:
                - conversation_id: ID da conversação
                - messages: Lista de mensagens
                - data: Dict com dados da conversa
                
        Returns:
            Resultado processado adequado ao tipo de entrada
            
        Raises:
            ValueError: Se os argumentos não puderem ser interpretados
        """
        # Garante inicialização
        await self._initialize()
        
        # Caso 1: Se o primeiro argumento for um dict, trata como dados da conversa
        if args and isinstance(args[0], dict):
            conversation_data = args[0]
            return await self._process_dict_data(conversation_data)
        
        # Caso 2: Se receber conversation_id e messages
        elif kwargs.get("conversation_id") and kwargs.get("messages"):
            return await self.process_conversation(
                conversation_id=kwargs["conversation_id"],
                messages=kwargs["messages"]
            )
        
        # Caso 3: Se receber data como kwarg
        elif kwargs.get("data"):
            return await self._process_dict_data(kwargs["data"])
        
        # Caso 4: Se receber argumentos posicionais para conversação
        elif len(args) >= 2:
            # Assume que o primeiro arg é conversation_id e o segundo é messages
            return await self.process_conversation(
                conversation_id=args[0],
                messages=args[1]
            )
        
        else:
            raise ValueError(
                "Argumentos inválidos. Forneça conversation_id e messages "
                "ou um dict com os dados da conversação."
            )
    
    async def _process_dict_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa dados da conversa fornecidos como dict.
        
        Args:
            data: Dict contendo conversation_id e messages
            
        Returns:
            Resultado processado
        """
        conversation_id = data.get("conversation_id")
        messages = data.get("messages")
        
        if not conversation_id or not messages:
            raise ValueError("Dict deve conter 'conversation_id' e 'messages'")
            
        return await self.process_conversation(
            conversation_id=conversation_id,
            messages=messages
        )

    async def process_conversation(
            self,
            conversation_id: str,
            messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Processa uma conversação completa.
        
        Args:
            conversation_id: ID único da conversação
            messages: Lista de mensagens da conversa
            
        Returns:
            Dicionário com resposta gerada e metadados
        """
        start_time = datetime.utcnow()

        try:
            # Garante inicialização
            await self._initialize()

            # Converte mensagens para formato LangChain
            langchain_messages = message_converter.to_langchain_messages(messages)

            # Obtém a última pergunta do usuário
            last_user_message = self._get_last_user_message(langchain_messages)

            if not last_user_message:
                raise ValueError("Nenhuma mensagem do usuário encontrada")

            # Busca contexto relevante
            context = await self._get_context(last_user_message.content)

            # Combina contexto com histórico
            full_messages = await self._prepare_messages(context, langchain_messages)

            # Processa com o modelo
            response = await self._chat_model.ainvoke(full_messages)

            # Prepara resposta
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000

            return {
                "id": conversation_id,
                "reply": response.content,
                "metadata": {
                    "processing_time_ms": round(processing_time, 2),
                    "model": settings.openai.model,
                    "context_documents": len(context) if context else 0
                }
            }

        except Exception as e:
            logger.error(f"Erro ao processar conversação {conversation_id}: {e}")
            raise

    def _get_last_user_message(self, messages: List[BaseMessage]) -> BaseMessage:
        """Obtém a última mensagem do usuário na conversa."""
        for message in reversed(messages):
            if message.type == "human":
                return message
        return None

    async def _get_context(self, query: str) -> List[Dict[str, Any]]:
        """
        Busca contexto relevante para a pergunta.
        
        Args:
            query: Pergunta para buscar contexto
            
        Returns:
            Lista de documentos relevantes
        """
        try:
            results = await self._vector_store.search(query)
            return results
        except Exception as e:
            logger.error(f"Erro ao buscar contexto: {e}")
            return []

    async def _prepare_messages(
            self,
            context: List[Dict[str, Any]],
            messages: List[BaseMessage]
    ) -> List[BaseMessage]:
        """
        Prepara mensagens com contexto formatado.
        
        Args:
            context: Contexto relevante encontrado
            messages: Mensagens originais
            
        Returns:
            Lista de mensagens preparadas para o modelo
        """
        # Formata o contexto
        formatted_context = self._format_context(context)

        # Prepara sistema prompt com contexto
        system_message = SystemMessagePromptTemplate(prompt=self._prompt_template)
        system_msg = system_message.format(context=formatted_context)

        # Combina sistema prompt com mensagens existentes
        return [system_msg] + messages

    def _format_context(self, context: List[Dict[str, Any]]) -> str:
        """
        Formata o contexto para uso no prompt.
        
        Args:
            context: Lista de documentos de contexto
            
        Returns:
            String formatada com o contexto
        """
        if not context:
            return "Nenhuma informação específica encontrada."

        formatted_docs = []
        for doc in context:
            if "content" in doc:
                source = doc.get("metadata", {}).get("source", "Fonte desconhecida")
                formatted_docs.append(f"Fonte: {source}\n{doc['content']}")

        return "\n\n".join(formatted_docs)


# Factory para criar instâncias do serviço
def create_conversation_service(vector_store: VectorStoreRepository) -> ConversationService:
    """
    Factory method para criar instância do serviço de conversação.
    
    Args:
        vector_store: Repositório de armazenamento vetorial
        
    Returns:
        Instância configurada do serviço
    """
    return ConversationService(vector_store)
