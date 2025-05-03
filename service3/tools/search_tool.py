"""
Ferramenta de busca de informações para o agente ReAct.

Esta ferramenta permite que o agente busque informações específicas
no banco de dados do restaurante usando busca semântica.
"""
import logging

from langchain_core.tools import tool

from service3.repositories.vector_store_repository import vector_store_repository

logger = logging.getLogger(__name__)


@tool
async def search_restaurant_information(query: str) -> str:
    """
    Busca informações no banco de dados do restaurante.
    
    Esta ferramenta permite pesquisar por informações específicas sobre:
    - Cardápio e pratos especiais
    - Horários de funcionamento
    - Políticas do restaurante
    - Informações sobre alergias e restrições alimentares
    - Eventos e promoções
    
    Args:
        query: Texto da consulta para buscar informações relacionadas
        
    Returns:
        str: Informações encontradas formatadas para o contexto
    """
    logger.info(f"Buscando informação sobre: {query}")

    try:
        # Busca documentos relevantes no vector store
        results = await vector_store_repository.search(query)

        if not results:
            return "Nenhuma informação específica encontrada sobre esse tópico. Posso ajudar com informações gerais."

        # Formata os resultados para apresentação
        formatted_info = []
        for result in results:
            source = result.get("source", "Fonte desconhecida")
            content = result.get("content", "")

            if content:
                formatted_info.append(f"Fonte: {source}\nInformação: {content}")

        # Combina todas as informações
        return "\n\n".join(formatted_info)

    except Exception as e:
        logger.error(f"Erro ao buscar informações: {e}")
        return f"Desculpe, houve um erro ao buscar informações. Posso ajudar de outra forma?"


# Registro da ferramenta para uso no agente
restaurant_search_tool = search_restaurant_information
