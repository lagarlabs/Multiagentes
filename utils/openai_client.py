"""
Cliente para interactuar con la API de OpenAI
"""

from typing import Dict, Any
from openai import OpenAI
from .ai_client_base import AIClientBase
import json
import logging
from loguru import logger
import re

class OpenAIClient(AIClientBase):
    """
    Cliente para interactuar con la API de OpenAI
    """
    
    def __init__(self, api_key: str):
        """
        Inicializa el cliente de OpenAI.
        
        Args:
            api_key (str): Clave API de OpenAI
        """
        super().__init__(api_key)
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-4o"  # Modelo específico del proyecto
        
    def analyze_project(self, project_description: str) -> Dict:
        """
        Analiza un proyecto y devuelve una estructura de tareas.
        
        Args:
            project_description (str): Descripción del proyecto
            
        Returns:
            Dict: Estructura de tareas generada
        """
        try:
            # Verificar la conexión
            response = self.verify_connection()
            if "error" in response:
                raise Exception(f"Error al verificar la conexión con OpenAI: {response['error']}")
                
            # Generar el prompt
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto en análisis de proyectos y gestión de tareas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            # Extraer el contenido de la respuesta
            content = response.choices[0].message.content
            
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
            logger.error(f"Error al analizar proyecto con OpenAI: {str(e)}")
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto programador que genera código de alta calidad."},
                    {"role": "user", "content": f"Genera código para esta tarea y devuelve un JSON con el código y explicaciones: {task_description}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Error al parsear la respuesta JSON: {result}")
                return {"error": "Formato de respuesta inválido"}
                
        except Exception as e:
            logger.error(f"Error al generar código con OpenAI: {str(e)}")
            return {"error": str(e)}
            
    def review_code(self, code: str, requirements: str) -> Dict:
        """
        Revisa código usando OpenAI.
        
        Args:
            code: Código a revisar
            requirements: Requerimientos del código
            
        Returns:
            Diccionario con el resultado de la revisión
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto programador que revisa código."},
                    {"role": "user", "content": f"Revisa este código según estos requerimientos y devuelve un JSON con los resultados:\nCódigo:\n{code}\nRequerimientos:\n{requirements}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Error al parsear la respuesta JSON: {result}")
                return {"error": "Formato de respuesta inválido"}
                
        except Exception as e:
            logger.error(f"Error al revisar código con OpenAI: {str(e)}")
            return {"error": str(e)}
            
    def test_code(self, code: str, test_requirements: str) -> Dict:
        """
        Genera tests usando OpenAI.
        
        Args:
            code: Código a testear
            test_requirements: Requerimientos de los tests
            
        Returns:
            Diccionario con los tests generados
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Eres un experto programador que genera tests."},
                    {"role": "user", "content": f"Genera tests para este código según estos requerimientos y devuelve un JSON con los tests:\nCódigo:\n{code}\nRequerimientos:\n{test_requirements}"}
                ],
                temperature=0.7,
                max_tokens=2000,
                n=1,
                stop=None
            )
            
            result = response.choices[0].message.content
            try:
                return json.loads(result)
            except json.JSONDecodeError:
                logger.error(f"Error al parsear la respuesta JSON: {result}")
                return {"error": "Formato de respuesta inválido"}
                
        except Exception as e:
            logger.error(f"Error al generar tests con OpenAI: {str(e)}")
            return {"error": str(e)}
            
    def verify_connection(self) -> Dict:
        """
        Verifica la conexión con la API de OpenAI.
        
        Returns:
            Dict: Estado de la conexión
        """
        try:
            # Intentar una operación simple para verificar la conexión
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test connection"}],
                max_tokens=5,
                temperature=0
            )
            return {"status": "success"}
        except Exception as e:
            logger.error(f"Error al verificar la conexión con OpenAI: {str(e)}")
            return {"status": "error", "error": str(e)}
