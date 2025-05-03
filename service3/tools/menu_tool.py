"""
Ferramenta de sugestões de menu para o agente ReAct.

Esta ferramenta fornece sugestões personalizadas de pratos
baseadas em preferências e restrições alimentares.
"""
import logging
from typing import Optional

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Banco de dados de sugestões (em produção, isso viria do vector store)
MENU_SUGGESTIONS = {
    "vegetarian": {
        "desc": "Opções vegetarianas",
        "items": [
            "Pizza Margherita",
            "Pasta Vegetariana",
            "Salada Grega",
            "Sanduíche de Vegetais Grelhados"
        ]
    },
    "vegan": {
        "desc": "Opções veganas",
        "items": [
            "Pizza Vegana (sem queijo)",
            "Pasta Primavera",
            "Salada da Casa (sem queijo)",
            "Curry de Vegetais"
        ]
    },
    "gluten-free": {
        "desc": "Opções sem glúten",
        "items": [
            "Pizza com massa sem glúten",
            "Todas as saladas (sem croutons)",
            "Frango ou peixe grelhado",
            "Pratos à base de arroz"
        ]
    },
    "popular": {
        "desc": "Pratos mais populares",
        "items": [
            "Pizza Margherita Clássica",
            "Pasta Alfredo com Frango",
            "Salada Caesar",
            "Salmão Grelhado Especial"
        ]
    },
    "daily-special": {
        "desc": "Especiais do dia",
        "items": [
            "Risotto de Cogumelos",
            "Peixe do Dia",
            "Pasta do Chef",
            "Promotion Combo"
        ]
    }
}


@tool
async def provide_menu_suggestions(dietary_preferences: Optional[str] = None) -> str:
    """
    Fornece sugestões de menu personalizadas.
    
    Esta ferramenta ajuda a recomendar pratos baseados em:
    - Restrições alimentares (vegetariano, vegano, sem glúten)
    - Preferências específicas
    - Pratos populares
    - Especiais do dia
    
    Args:
        dietary_preferences: Preferências ou restrições alimentares (opcional)
            Valores aceitos: "vegetarian", "vegan", "gluten-free", "popular", "daily-special"
        
    Returns:
        str: Sugestões formatadas de pratos
    """
    logger.info(f"Gerando sugestões para preferências: {dietary_preferences}")

    # Se não há preferência específica, mostra opções populares
    if not dietary_preferences:
        dietary_preferences = "popular"

    # Normaliza a entrada
    preference_key = dietary_preferences.lower().replace("-", "_").replace(" ", "_")

    # Busca sugestões apropriadas
    if preference_key in MENU_SUGGESTIONS:
        suggestions = MENU_SUGGESTIONS[preference_key]
    else:
        # Fallback para opções populares se preferência não é reconhecida
        suggestions = MENU_SUGGESTIONS["popular"]

    # Formata a resposta
    response = f"**{suggestions['desc']}:**\n"
    for i, item in enumerate(suggestions['items'], 1):
        response += f"\n{i}. {item}"

    # Adiciona nota adicional para restrições alimentares
    if preference_key in ["vegetarian", "vegan", "gluten_free"]:
        response += "\n\nNota: Todos os pratos mencionados são verificados para atender às suas restrições alimentares."
        response += "\nPor favor, informe qualquer alergia específica que você possa ter."

    return response


# Mapeamento de alergias para ferramentas adicionais
ALLERGY_INFO = {
    "nuts": "amendoim e nozes",
    "dairy": "laticínios",
    "shellfish": "frutos do mar",
    "soy": "soja",
    "eggs": "ovos",
    "wheat": "trigo/glúten"
}


@tool
async def check_allergens(dish_name: str, allergen: str) -> str:
    """
    Verifica se um prato contém alérgenos específicos.
    
    Args:
        dish_name: Nome do prato a ser verificado
        allergen: Tipo de alérgeno (nuts, dairy, shellfish, soy, eggs, wheat)
        
    Returns:
        str: Informação sobre presença de alérgenos
    """
    logger.info(f"Verificando alérgenos em {dish_name}: {allergen}")

    # Em produção, isso consultaria um banco de dados detalhado
    allergen_name = ALLERGY_INFO.get(allergen.lower(), allergen)

    # Resposta padrão (em produção seria mais específica)
    return f"Para verificar se '{dish_name}' contém {allergen_name}, precisarei consultar nossa base de dados detalhada. Recomendo informar ao garçom sobre sua alergia para garantir total segurança."


# Exportação das ferramentas
menu_suggestion_tool = provide_menu_suggestions
allergen_check_tool = check_allergens
