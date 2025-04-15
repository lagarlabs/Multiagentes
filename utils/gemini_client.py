"""
Módulo para manejar las interacciones con la API de Google Gemini.
"""
import os
import json
import re
from typing import Dict, List, Optional, Any
from google import genai
from .ai_client_base import AIClientBase
from loguru import logger

class GeminiClient(AIClientBase):
    """Cliente para interactuar con la API de Google Gemini."""
    
    def __init__(self, api_key: str, model: str = "gemini-2.5-pro-exp-03-25"):
        """
        Inicializa el cliente de Google Gemini.
        
        Args:
            api_key: API key de Google
            model: Modelo de Gemini a utilizar (default: gemini-2.5-pro-exp-03-25)
        """
        super().__init__(api_key)
        self.model = model
        self.client = genai.Client(api_key=api_key)
        
    def _generate_content(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Genera contenido utilizando el modelo de Gemini.
        
        Args:
            prompt: Prompt para el modelo
            system_instruction: Instrucción de sistema opcional
            
        Returns:
            Contenido generado
            
        Raises:
            Exception: Si hay un error en la generación
        """
        try:
            # Configurar el contenido según haya o no instrucción de sistema
            if system_instruction:
                contents = [
                    {"role": "system", "parts": [{"text": system_instruction}]},
                    {"role": "user", "parts": [{"text": prompt}]}
                ]
            else:
                contents = [{"role": "user", "parts": [{"text": prompt}]}]
            
            # Generar respuesta
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                generation_config={"temperature": 0.2, "max_output_tokens": 8000}
            )
            
            return response.text
        except Exception as e:
            logger.error(f"Error generando contenido con Gemini: {str(e)}")
            raise Exception(f"Error de API de Gemini: {str(e)}")
            
    def analyze_project(self, project_description: str) -> Dict:
        """
        Analiza un proyecto y devuelve una estructura de tareas.
        
        Args:
            project_description (str): Descripción del proyecto
            
        Returns:
            Dict: Estructura de tareas generada
        """
        try:
            # Generar el prompt
            system_instruction = """Eres un experto en análisis de proyectos de software. Tu tarea es analizar proyectos y dividirlos en tareas manejables."""
            
            prompt = f"""
            Analiza el siguiente proyecto y genera una estructura de tareas en formato JSON.
            Cada tarea debe tener un id único, descripción, tipo y habilidades requeridas.
            
            Proyecto: {project_description}
            
            Formato esperado:
            {{
                "project": "Nombre del proyecto",
                "tasks": [
                    {{
                        "id": 1,
                        "type": "development|testing|documentation",
                        "description": "Descripción de la tarea",
                        "required_skills": ["skill1", "skill2"],
                        "dependencies": []
                    }}
                ]
            }}
            """
            
            # Hacer la llamada a la API
            content = self._generate_content(prompt, system_instruction)
            
            # Buscar el JSON en el contenido
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                raise Exception("No se encontró JSON en la respuesta")
                
            json_str = json_match.group()
            
            # Intentar parsear el JSON
            try:
                result = json.loads(json_str)
            except json.JSONDecodeError as e:
                logger.error(f"Error al parsear la respuesta JSON: {json_str}")
                logger.error(f"Error específico: {str(e)}")
                raise Exception("Formato de respuesta inválido")
            
            # Validar la estructura del resultado
            if not isinstance(result, dict):
                raise Exception("El resultado no es un diccionario")
                
            if "project" not in result or "tasks" not in result:
                raise Exception("Faltan campos requeridos en el resultado")
                
            if not isinstance(result["tasks"], list):
                raise Exception("El campo 'tasks' no es una lista")
                
            # Validar cada tarea
            for task in result["tasks"]:
                if not isinstance(task, dict):
                    raise Exception("Una tarea no es un diccionario")
                    
                if "id" not in task:
                    task["id"] = len(result["tasks"])
                    
                if "type" not in task:
                    task["type"] = "development"
                    
                if "required_skills" not in task:
                    task["required_skills"] = []
                    
                if "dependencies" not in task:
                    task["dependencies"] = []
            
            return result
            
        except Exception as e:
            logger.error(f"Error al analizar proyecto con Gemini: {str(e)}")
            return {"error": str(e)}
            
    def generate_code(self, task_description: str) -> Dict:
        """
        Genera código basado en una descripción de tarea.
        
        Args:
            task_description (str): Descripción de la tarea
            
        Returns:
            Dict: Diccionario con el código generado
        """
        try:
            system_instruction = """Eres un experto programador que genera código de alta calidad. Tu tarea es generar código basado en descripciones de tareas.
            
            Reglas para el código generado:
            1. Debe ser código funcional y completo
            2. Debe incluir todos los imports necesarios
            3. Debe estar bien documentado con comentarios en español
            4. Debe seguir las mejores prácticas de programación
            5. Debe ser eficiente y mantenible
            6. No incluyas explicaciones fuera del código
            7. No uses backticks o markdown"""
            
            prompt = f"""Genera código para la siguiente tarea y devuelve un JSON con el código y explicaciones:

{task_description}

IMPORTANTE:
1. El resultado debe ser un JSON válido con esta estructura:
{{
    "code": "código completo aquí",
    "explanation": "explicación del código"
}}
2. Incluye todos los imports necesarios
3. Documenta el código con comentarios en español
4. Asegúrate de que el código sea funcional y completo"""
            
            content = self._generate_content(prompt, system_instruction)
            
            # Buscar el JSON en el contenido
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                # Si no se encuentra JSON, envolver el contenido como código
                return {
                    "code": content.strip(),
                    "explanation": "Código generado por Gemini"
                }
                
            json_str = json_match.group()
            
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                # En caso de error parsing JSON, devolver el contenido completo
                return {
                    "code": content.strip(),
                    "explanation": "Código generado por Gemini"
                }
                
        except Exception as e:
            logger.error(f"Error al generar código con Gemini: {str(e)}")
            return {"error": str(e)}
            
    def review_code(self, code: str, requirements: str) -> Dict:
        """
        Revisa código usando Gemini.
        
        Args:
            code: Código a revisar
            requirements: Requerimientos del código
            
        Returns:
            Diccionario con el resultado de la revisión
        """
        try:
            system_instruction = "Eres un experto programador que revisa código."
            prompt = f"""Revisa este código según estos requerimientos y devuelve un JSON con los resultados:

Código:
{code}

Requerimientos:
{requirements}

El resultado debe ser un JSON con esta estructura:
{{
    "issues": [
        {{
            "type": "error|warning|suggestion",
            "description": "Descripción del problema",
            "line": "número de línea o rango afectado (opcional)"
        }}
    ],
    "overall_quality": "buena|regular|mala",
    "suggestions": [
        "Sugerencia 1",
        "Sugerencia 2"
    ]
}}"""
            
            content = self._generate_content(prompt, system_instruction)
            
            # Intentar extraer el JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                raise Exception("No se encontró JSON en la respuesta")
                
            json_str = json_match.group()
            
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                logger.error(f"Error al parsear la respuesta JSON: {content}")
                # Formato fallback en caso de error
                return {
                    "issues": [],
                    "overall_quality": "indeterminada",
                    "suggestions": ["No se pudo analizar la respuesta del modelo"]
                }
                
        except Exception as e:
            logger.error(f"Error al revisar código con Gemini: {str(e)}")
            return {"error": str(e)}
            
    def test_code(self, code: str, test_requirements: str) -> Dict:
        """
        Genera tests usando Gemini.
        
        Args:
            code: Código a testear
            test_requirements: Requerimientos de los tests
            
        Returns:
            Diccionario con los tests generados
        """
        try:
            system_instruction = "Eres un experto programador que genera tests."
            prompt = f"""Genera tests para este código según estos requerimientos y devuelve un JSON con los tests:

Código:
{code}

Requerimientos:
{test_requirements}

El resultado debe ser un JSON con esta estructura:
{{
    "tests": [
        {{
            "name": "nombre_del_test",
            "description": "descripción del test",
            "code": "código del test"
        }}
    ],
    "setup": "código de configuración necesario para ejecutar los tests (opcional)"
}}"""
            
            content = self._generate_content(prompt, system_instruction)
            
            # Intentar extraer el JSON
            json_match = re.search(r'\{[\s\S]*\}', content)
            if not json_match:
                raise Exception("No se encontró JSON en la respuesta")
                
            json_str = json_match.group()
            
            try:
                result = json.loads(json_str)
                return result
            except json.JSONDecodeError:
                logger.error(f"Error al parsear la respuesta JSON: {content}")
                return {"error": "Formato de respuesta inválido"}
                
        except Exception as e:
            logger.error(f"Error al generar tests con Gemini: {str(e)}")
            return {"error": str(e)}
            
    def verify_connection(self) -> Dict:
        """
        Verifica la conexión con la API de Gemini.
        
        Returns:
            Dict: Estado de la conexión
        """
        try:
            # Intentar una operación simple para verificar la conexión
            response = self.client.models.generate_content(
                model=self.model,
                contents=[{"role": "user", "parts": [{"text": "test connection"}]}],
                generation_config={"max_output_tokens": 5}
            )
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error al verificar la conexión con Gemini: {str(e)}")
            return {"status": "error", "error": str(e)}