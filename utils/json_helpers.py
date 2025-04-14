"""
Utilidades para el manejo de respuestas JSON de los agentes.
"""

import json
import logging
from typing import Dict, Any, Optional

def extract_json_from_markdown(text: str) -> str:
    """
    Extrae el contenido JSON de una respuesta en formato markdown.
    
    Args:
        text: Texto que puede contener bloques de código markdown
        
    Returns:
        Texto JSON limpio
    """
    text = text.strip()
    
    # Caso 1: JSON dentro de bloques ```json
    if "```json" in text:
        parts = text.split("```json")
        if len(parts) > 1:
            json_part = parts[1].split("```")[0].strip()
            return json_part
    
    # Caso 2: JSON dentro de bloques ``` genéricos
    elif "```" in text:
        parts = text.split("```")
        if len(parts) > 1:
            json_part = parts[1].strip()
            return json_part
    
    # Caso 3: Suponer que todo el texto es JSON
    return text

def parse_agent_response(response_content: str, error_context: str = "respuesta del agente") -> Dict[str, Any]:
    """
    Parsea la respuesta de un agente a formato JSON.
    
    Args:
        response_content: Contenido de la respuesta del agente
        error_context: Contexto para el mensaje de error
        
    Returns:
        Diccionario con datos parseados
    
    Raises:
        ValueError: Si no se puede parsear la respuesta como JSON
    """
    try:
        # Extraer contenido JSON de markdown si es necesario
        json_str = extract_json_from_markdown(response_content)
        
        # Parsear el JSON
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logging.error(f"Error al parsear {error_context}: {str(e)}")
        logging.error(f"Contenido: {response_content}")
        raise ValueError(f"La {error_context} no es un JSON válido: {str(e)}")
    except Exception as e:
        logging.error(f"Error inesperado al procesar {error_context}: {str(e)}")
        raise ValueError(f"Error al procesar {error_context}: {str(e)}")

def validate_required_fields(data: Dict[str, Any], required_fields: list, context: str = "objeto") -> None:
    """
    Valida que un diccionario contenga todos los campos requeridos.
    
    Args:
        data: Diccionario a validar
        required_fields: Lista de campos requeridos
        context: Contexto para el mensaje de error
        
    Raises:
        ValueError: Si falta algún campo requerido
    """
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Campo requerido '{field}' no encontrado en {context}")