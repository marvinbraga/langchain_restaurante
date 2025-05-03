# tools/__init__.py - Exporta todas as ferramentas
from service3.tools.menu_tool import (
    menu_suggestion_tool,
    allergen_check_tool,
    provide_menu_suggestions,
    check_allergens
)
from service3.tools.search_tool import restaurant_search_tool, search_restaurant_information

__all__ = [
    'restaurant_search_tool',
    'search_restaurant_information',
    'menu_suggestion_tool',
    'allergen_check_tool',
    'provide_menu_suggestions',
    'check_allergens'
]
