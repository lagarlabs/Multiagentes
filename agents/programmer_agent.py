"""
Agente Programador del sistema multiagentes.
Este agente se encarga de generar código basado en las especificaciones.
"""

from typing import Dict, List, Optional
from loguru import logger
import json
from datetime import datetime
import os
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeekChat

from utils.json_helpers import parse_agent_response
from utils.config_manager import ConfigManager

class ProgrammerAgent:
    """Agente programador que genera código basado en especificaciones"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente programador
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un ingeniero de software experto con años de experiencia en desarrollo.
                Tu objetivo es generar código de alta calidad que cumpla con las especificaciones.
                
                Tus responsabilidades incluyen:
                1. Generar código limpio y mantenible
                2. Crear documentación clara y completa
                3. Implementar pruebas unitarias
                4. Seguir las mejores prácticas de desarrollo
                5. Optimizar el rendimiento cuando sea necesario
                
                Tu estilo de programación es:
                - Modular y reutilizable
                - Bien documentado y legible
                - Eficiente y optimizado
                - Siguiendo principios SOLID\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos en detalle
                2. Diseña una solución modular y escalable
                3. Implementa el código siguiendo buenas prácticas
                4. Documenta todas las funciones y clases
                5. Crea pruebas unitarias exhaustivas
                6. Optimiza el rendimiento cuando sea necesario\
            """),
            expected_output=dedent("""\
                {
                    "code": {
                        "files": [
                            {
                                "name": "nombre_archivo.py",
                                "content": "código fuente",
                                "description": "descripción del archivo"
                            }
                        ],
                        "dependencies": [
                            {
                                "name": "nombre_paquete",
                                "version": "versión"
                            }
                        ]
                    },
                    "documentation": {
                        "overview": "descripción general",
                        "setup": "instrucciones de instalación",
                        "usage": "ejemplos de uso",
                        "api": [
                            {
                                "name": "nombre_función",
                                "description": "descripción",
                                "parameters": [],
                                "returns": "valor retornado"
                            }
                        ]
                    },
                    "tests": {
                        "unit_tests": [
                            {
                                "name": "nombre_test",
                                "description": "descripción",
                                "code": "código del test"
                            }
                        ],
                        "coverage": {
                            "percentage": 0-100,
                            "missing": []
                        }
                    }
                }\
            """),
            markdown=True
        )
        
        # Inicializar el agente de razonamiento con DeepSeek
        self.reasoning_agent = Agent(
            model=DeepSeekChat(id=self.config.get("reasoning_model")),
            description=dedent("""\
                Eres un experto en diseño de software que utiliza razonamiento paso a paso
                para diseñar soluciones elegantes y eficientes.\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos paso a paso
                2. Identifica los componentes principales
                3. Diseña la arquitectura del sistema
                4. Define las interfaces y contratos
                5. Proporciona justificación de decisiones\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.current_task = None
        logger.info("Agente Programador inicializado")

    async def generate_implementation(self, requirements: Dict) -> Dict:
        """
        Genera una implementación basada en los requerimientos
        
        Args:
            requirements (Dict): Requerimientos del código a generar
            
        Returns:
            Dict: Implementación generada
        """
        try:
            # Primero usar el agente de razonamiento para diseñar la solución
            design_prompt = f"""
            Analiza los siguientes requerimientos y diseña una solución:
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            RESTRICCIONES:
            {requirements.get('constraints', '')}
            
            TECNOLOGÍAS:
            {requirements.get('technologies', '')}
            """
            
            design_response = await self.reasoning_agent.arun(design_prompt)
            
            # Usar el diseño para generar la implementación
            implementation_prompt = f"""
            Genera una implementación basada en el siguiente diseño:
            
            DISEÑO:
            {design_response.content}
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            RESTRICCIONES:
            {requirements.get('constraints', '')}
            
            TECNOLOGÍAS:
            {requirements.get('technologies', '')}
            
            Genera una implementación completa siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(implementation_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de implementación")
                return {
                    'status': 'success',
                    'implementation': result,
                    'design': design_response.content,
                    'generated_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al generar implementación: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def generate_tests(self, implementation: Dict) -> Dict:
        """
        Genera pruebas unitarias para una implementación
        
        Args:
            implementation (Dict): Implementación para la que generar pruebas
            
        Returns:
            Dict: Pruebas generadas
        """
        try:
            prompt = f"""
            Genera pruebas unitarias para la siguiente implementación:
            
            CÓDIGO:
            {implementation.get('code', '')}
            
            DOCUMENTACIÓN:
            {implementation.get('documentation', '')}
            
            Genera pruebas unitarias siguiendo el formato JSON especificado.
            Asegúrate de cubrir:
            1. Casos normales
            2. Casos borde
            3. Manejo de errores
            4. Validación de entrada
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de pruebas")
                return {
                    'status': 'success',
                    'tests': result,
                    'generated_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al generar pruebas: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def refactor_code(self, implementation: Dict, feedback: Dict) -> Dict:
        """
        Refactoriza código basado en el feedback recibido
        
        Args:
            implementation (Dict): Implementación a refactorizar
            feedback (Dict): Feedback con sugerencias de mejora
            
        Returns:
            Dict: Implementación refactorizada
        """
        try:
            prompt = f"""
            Refactoriza el siguiente código basado en el feedback recibido:
            
            CÓDIGO ORIGINAL:
            {implementation.get('code', '')}
            
            FEEDBACK:
            {feedback.get('suggestions', '')}
            
            PROBLEMAS IDENTIFICADOS:
            {feedback.get('issues', '')}
            
            Genera una nueva implementación refactorizada siguiendo el formato JSON especificado.
            Asegúrate de:
            1. Abordar todos los problemas identificados
            2. Implementar las sugerencias de mejora
            3. Mantener la funcionalidad original
            4. Documentar los cambios realizados
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de refactorización")
                return {
                    'status': 'success',
                    'implementation': result,
                    'refactored_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al refactorizar código: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente programador
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            'status': 'active',
            'current_task': self.current_task,
            'working_dir': str(self.working_dir)
        }