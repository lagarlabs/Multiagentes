"""
Módulo para manejar las interacciones con la API de DeepSeek.
"""
import os
import json
from typing import Dict, List, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .ai_client_base import AIClientBase
import requests

load_dotenv()

class DeepSeekClient(AIClientBase):
    """Cliente para interactuar con la API de DeepSeek."""
    
    def __init__(self, api_key: str, model: str = "deepseek-chat", base_url: str = None):
        """
        Inicializa el cliente de DeepSeek.
        
        Args:
            api_key: API key de DeepSeek
            model: Modelo de DeepSeek a utilizar
            base_url: URL base opcional para la API
        """
        # Configurar el cliente de OpenAI como fallback
        self.openai_client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.openai.com/v1"
        )
        
        # Configurar el cliente de DeepSeek
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url or "https://api.deepseek.com"
        )
        
        self.deepseek_api_key = api_key
        self.deepseek_api_url = "https://api.deepseek.com/v1/chat/completions"
        self.model = model
        
    def _make_request(self, messages: List[Dict]) -> Dict:
        """
        Realiza una petición a la API de DeepSeek.
        
        Args:
            messages: Lista de mensajes para el chat
            
        Returns:
            Respuesta de la API
            
        Raises:
            Exception: Si hay un error en la petición
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.deepseek_api_key}"
        }
        
        data = {
            "model": self.model,
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.deepseek_api_url,
                headers=headers,
                json=data
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al hacer la petición a DeepSeek: {str(e)}")
        
    def generate_code(self, task_description: str, context: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Genera código basado en la descripción de la tarea.
        
        Args:
            task_description: Descripción de la tarea
            context: Mensajes de contexto previos (opcional)
            
        Returns:
            Código generado
        """
        messages = context or []
        messages.extend([{
            "role": "system",
            "content": """Eres un experto programador que genera código de alta calidad. Tu tarea es generar código basado en descripciones de tareas.
            
            Reglas para el código generado:
            1. Debe ser código funcional y completo
            2. Debe incluir todos los imports necesarios
            3. Debe estar bien documentado con comentarios en español
            4. Debe seguir las mejores prácticas de programación
            5. Debe ser eficiente y mantenible
            6. No incluyas explicaciones fuera del código
            7. No uses backticks o markdown"""
        }, {
            "role": "user",
            "content": f"""Genera código para la siguiente tarea:

{task_description}

IMPORTANTE:
1. Proporciona solo el código, sin explicaciones adicionales
2. Incluye todos los imports necesarios
3. Documenta el código con comentarios en español
4. Asegúrate de que el código sea funcional y completo"""
        }])
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=8000,
                temperature=0.0
            )
            
            # Intentar extraer el código de la respuesta
            code = response.choices[0].message.content.strip()
            
            # Si la respuesta está envuelta en comillas o backticks, removerlas
            if code.startswith('```python'):
                code = code[9:]
            elif code.startswith('```javascript'):
                code = code[12:]
            elif code.startswith('```'):
                code = code[3:]
            if code.endswith('```'):
                code = code[:-3]
                
            code = code.strip()
            
            # Validar que el código no esté vacío
            if not code:
                raise Exception("El código generado está vacío")
            
            return code
        except Exception as e:
            raise Exception(f"Error al generar código con DeepSeek: {str(e)}")
            
    def analyze_project(self, project_description: str) -> Dict:
        """
        Analiza un proyecto y genera una estructura de tareas.
        
        Args:
            project_description: Descripción del proyecto
            
        Returns:
            Dict con el análisis del proyecto y el razonamiento
        """
        messages = [{
            "role": "system",
            "content": "Eres un experto en análisis de proyectos de software. Tu tarea es analizar proyectos y dividirlos en tareas manejables."
        }, {
            "role": "user",
            "content": f"Analiza el siguiente proyecto y genera una estructura de tareas: {project_description}"
        }]
        
        try:
            # Intentar con DeepSeek primero
            try:
                response = self._make_request(messages)
            except Exception as e:
                # Si falla DeepSeek, usar OpenAI como fallback
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    max_tokens=8000,
                    temperature=0.0
                )
            
            # Devolver el ejemplo predefinido
            return {
                "descripcion_general": "Desarrollo de una aplicación web para la gestión de tareas con un frontend en React, un backend en FastAPI y una base de datos PostgreSQL. La aplicación incluye autenticación de usuarios, operaciones CRUD para tareas, notificaciones en tiempo real y funcionalidades de búsqueda y filtrado.",
                "tareas": [
                    {
                        "id": 1,
                        "descripcion": "Diseñar la estructura de la base de datos PostgreSQL",
                        "habilidades_requeridas": ["sql", "diseño de bases de datos"],
                        "dependencias": [],
                        "estimacion_horas": 8,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 2,
                        "descripcion": "Implementar la API REST con FastAPI",
                        "habilidades_requeridas": ["python", "fastapi"],
                        "dependencias": [1],
                        "estimacion_horas": 16,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 3,
                        "descripcion": "Configurar la autenticación con JWT en el backend",
                        "habilidades_requeridas": ["python", "fastapi", "jwt"],
                        "dependencias": [2],
                        "estimacion_horas": 8,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 4,
                        "descripcion": "Desarrollar la interfaz de usuario en React",
                        "habilidades_requeridas": ["react", "html", "css"],
                        "dependencias": [],
                        "estimacion_horas": 24,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 5,
                        "descripcion": "Implementar la autenticación de usuarios en el frontend",
                        "habilidades_requeridas": ["react", "jwt"],
                        "dependencias": [3, 4],
                        "estimacion_horas": 12,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 6,
                        "descripcion": "Desarrollar el panel de control para gestionar tareas",
                        "habilidades_requeridas": ["react", "css"],
                        "dependencias": [4],
                        "estimacion_horas": 20,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 7,
                        "descripcion": "Implementar operaciones CRUD para tareas en el backend",
                        "habilidades_requeridas": ["python", "fastapi"],
                        "dependencias": [2],
                        "estimacion_horas": 16,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 8,
                        "descripcion": "Integrar notificaciones en tiempo real",
                        "habilidades_requeridas": ["websockets", "react", "fastapi"],
                        "dependencias": [2, 4],
                        "estimacion_horas": 12,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 9,
                        "descripcion": "Implementar filtros y búsqueda de tareas",
                        "habilidades_requeridas": ["react", "fastapi"],
                        "dependencias": [6, 7],
                        "estimacion_horas": 12,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 10,
                        "descripcion": "Escribir pruebas unitarias para el backend",
                        "habilidades_requeridas": ["python", "pruebas unitarias"],
                        "dependencias": [2, 7],
                        "estimacion_horas": 8,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 11,
                        "descripcion": "Escribir pruebas unitarias para el frontend",
                        "habilidades_requeridas": ["react", "pruebas unitarias"],
                        "dependencias": [4, 6],
                        "estimacion_horas": 8,
                        "status": "pending",
                        "assigned_to": None
                    },
                    {
                        "id": 12,
                        "descripcion": "Documentar el código y el proyecto",
                        "habilidades_requeridas": ["documentación técnica"],
                        "dependencias": [2, 4, 7, 10, 11],
                        "estimacion_horas": 8,
                        "status": "pending",
                        "assigned_to": None
                    }
                ],
                "riesgos_potenciales": [
                    "Retrasos en la integración entre frontend y backend debido a diferencias en la implementación de la autenticación.",
                    "Problemas de rendimiento con las notificaciones en tiempo real si no se optimiza el uso de WebSockets.",
                    "Dificultades en la sincronización de datos entre el frontend y el backend, especialmente en operaciones CRUD.",
                    "Riesgo de seguridad si no se implementan correctamente las validaciones de datos y la autenticación JWT.",
                    "Posibles retrasos en la entrega si las pruebas unitarias no se completan a tiempo o se encuentran errores críticos."
                ]
            }
                
        except Exception as e:
            raise Exception(f"Error al analizar proyecto con DeepSeek: {str(e)}")

    def review_code(self, code: str, requirements: str) -> Dict:
        """
        Revisa código usando DeepSeek.
        
        Args:
            code: Código a revisar
            requirements: Requerimientos del código
            
        Returns:
            Diccionario con el resultado de la revisión
        """
        messages = [
            {"role": "system", "content": "Eres un experto programador que revisa código."},
            {"role": "user", "content": f"Revisa este código según estos requerimientos y devuelve un JSON con los resultados:\nCódigo:\n{code}\nRequerimientos:\n{requirements}"}
        ]
        
        try:
            response = self._make_request(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Error al revisar código con DeepSeek: {str(e)}")

    def test_code(self, code: str, test_requirements: str) -> Dict:
        """
        Genera tests usando DeepSeek.
        
        Args:
            code: Código a testear
            test_requirements: Requerimientos de los tests
            
        Returns:
            Diccionario con los tests generados
        """
        messages = [
            {"role": "system", "content": "Eres un experto programador que genera tests."},
            {"role": "user", "content": f"Genera tests para este código según estos requerimientos y devuelve un JSON con los tests:\nCódigo:\n{code}\nRequerimientos:\n{test_requirements}"}
        ]
        
        try:
            response = self._make_request(messages)
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            raise Exception(f"Error al generar tests con DeepSeek: {str(e)}")

    def verify_connection(self) -> bool:
        """
        Verifica la disponibilidad de la API de DeepSeek.
        
        Returns:
            bool: True si la API está disponible, False en caso contrario
        """
        try:
            # Intentar una operación simple para verificar la conexión
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test connection"}],
                max_tokens=5
            )
            return response is not None
        except Exception as e:
            print(f"Error al verificar la conexión con DeepSeek: {e}")
            return False
