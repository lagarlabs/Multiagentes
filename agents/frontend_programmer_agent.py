"""
Agente Programador Frontend del sistema multiagentes.
Este agente se especializa en desarrollo frontend.
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

class FrontendProgrammerAgent:
    """Agente programador especializado en desarrollo frontend"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente programador frontend
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un ingeniero de software frontend experto con años de experiencia.
                Tu objetivo es generar interfaces de usuario atractivas, intuitivas y funcionales.
                
                Tus responsabilidades incluyen:
                1. Diseñar e implementar interfaces de usuario
                2. Desarrollar componentes reutilizables
                3. Optimizar la experiencia del usuario
                4. Asegurar diseños responsivos
                5. Implementar animaciones y transiciones fluidas
                
                Tu estilo de programación es:
                - Modular y reutilizable
                - Limpio y bien organizado
                - Optimizado para rendimiento
                - Accesible y siguiendo estándares web
                - Bien documentado y testeado\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos visuales y funcionales
                2. Diseña la arquitectura de componentes
                3. Implementa interfaces responsivas y accesibles
                4. Optimiza el rendimiento de la UI
                5. Integra con APIs backend
                6. Documenta componentes y su uso
                7. Incluye pruebas de componentes\
            """),
            expected_output=dedent("""\
                {
                    "frontend": {
                        "architecture": {
                            "description": "descripción de la arquitectura",
                            "components": ["componente1", "componente2"]
                        },
                        "ui_design": {
                            "theme": {
                                "colors": {},
                                "typography": {},
                                "spacing": {}
                            },
                            "components": [
                                {
                                    "name": "nombre_componente",
                                    "description": "descripción",
                                    "props": [],
                                    "screenshot": "descripción de la apariencia"
                                }
                            ],
                            "pages": [
                                {
                                    "name": "nombre_página",
                                    "route": "/ruta",
                                    "components": [],
                                    "description": "descripción"
                                }
                            ]
                        },
                        "files": [
                            {
                                "name": "nombre_archivo.js",
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
                        "component_docs": "documentación de componentes",
                        "examples": "ejemplos de uso"
                    },
                    "tests": {
                        "component_tests": [
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
                Eres un arquitecto de UI/UX que utiliza razonamiento paso a paso
                para diseñar interfaces atractivas, intuitivas y funcionales.\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos de interfaz paso a paso
                2. Identifica patrones de diseño adecuados
                3. Considera la experiencia de usuario
                4. Planifica la estructura de componentes
                5. Evalúa opciones tecnológicas para implementación\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.current_task = None
        logger.info("Agente Programador Frontend inicializado")

    async def design_ui(self, requirements: Dict) -> Dict:
        """
        Diseña la interfaz de usuario del proyecto
        
        Args:
            requirements (Dict): Requerimientos del proyecto
            
        Returns:
            Dict: Diseño de la interfaz de usuario
        """
        try:
            # Usar el agente de razonamiento para diseñar la UI
            design_prompt = f"""
            Diseña una interfaz de usuario basada en los siguientes requerimientos:
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            TIPO DE APLICACIÓN:
            {requirements.get('application_type', '')}
            
            USUARIOS OBJETIVO:
            {requirements.get('target_users', [])}
            
            FUNCIONALIDADES PRINCIPALES:
            {requirements.get('features', [])}
            
            Proporciona un diseño detallado siguiendo un razonamiento paso a paso:
            1. Evaluar las necesidades del usuario
            2. Planificar la arquitectura de información
            3. Diseñar el flujo de usuario
            4. Considerar principios de accesibilidad
            5. Seleccionar patrones de diseño adecuados
            """
            
            design_response = await self.reasoning_agent.arun(design_prompt)
            
            # Usar el diseño para generar el diseño detallado de UI
            ui_prompt = f"""
            Genera un diseño de interfaz detallado basado en:
            
            DISEÑO CONCEPTUAL:
            {design_response.content}
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            Genera una especificación de diseño completa siguiendo el formato JSON especificado.
            Incluye:
            1. Sistema de diseño (colores, tipografía, espaciado)
            2. Estructura de páginas y componentes
            3. Estados de componentes (normal, hover, error, etc.)
            4. Consideraciones de responsive design
            5. Animaciones y transiciones
            """
            
            response = await self.agent.arun(ui_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de diseño UI")
                return {
                    'status': 'success',
                    'ui_design': result,
                    'reasoning': design_response.content,
                    'designed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al diseñar UI: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def implement_components(self, ui_design: Dict, frontend_framework: str) -> Dict:
        """
        Implementa los componentes de la interfaz de usuario
        
        Args:
            ui_design (Dict): Diseño de la interfaz
            frontend_framework (str): Framework de frontend a utilizar
            
        Returns:
            Dict: Implementación de los componentes
        """
        try:
            # Usar el agente de razonamiento para diseñar la arquitectura de componentes
            component_arch_prompt = f"""
            Diseña una arquitectura de componentes basada en el siguiente diseño UI y framework:
            
            DISEÑO UI:
            {json.dumps(ui_design, indent=2)}
            
            FRAMEWORK: {frontend_framework}
            
            Proporciona una arquitectura detallada siguiendo un razonamiento paso a paso:
            1. Identificar componentes reutilizables
            2. Establecer jerarquía de componentes
            3. Definir props y estado de cada componente
            4. Planificar gestión de estado
            5. Considerar optimizaciones de rendimiento
            """
            
            arch_response = await self.reasoning_agent.arun(component_arch_prompt)
            
            # Usar la arquitectura para implementar los componentes
            implementation_prompt = f"""
            Implementa los componentes basados en la siguiente arquitectura:
            
            ARQUITECTURA DE COMPONENTES:
            {arch_response.content}
            
            DISEÑO UI:
            {json.dumps(ui_design, indent=2)}
            
            FRAMEWORK: {frontend_framework}
            
            Genera una implementación completa siguiendo el formato JSON especificado.
            Incluye:
            1. Código de cada componente
            2. Tests para componentes clave
            3. Documentación de uso
            4. Ejemplos de integración
            5. Consideraciones de rendimiento
            """
            
            response = await self.agent.arun(implementation_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de implementación de componentes")
                return {
                    'status': 'success',
                    'components': result,
                    'architecture': arch_response.content,
                    'implemented_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al implementar componentes: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def integrate_with_api(self, components: Dict, api_spec: Dict) -> Dict:
        """
        Integra los componentes frontend con la API backend
        
        Args:
            components (Dict): Componentes frontend implementados
            api_spec (Dict): Especificación de la API
            
        Returns:
            Dict: Componentes integrados con la API
        """
        try:
            prompt = f"""
            Integra los siguientes componentes frontend con la API backend:
            
            COMPONENTES FRONTEND:
            {json.dumps(components, indent=2)}
            
            ESPECIFICACIÓN API:
            {json.dumps(api_spec, indent=2)}
            
            Genera una implementación integrada siguiendo el formato JSON especificado.
            Incluye:
            1. Servicio de API / cliente HTTP
            2. Manejo de estados de carga
            3. Gestión de errores
            4. Caché y optimizaciones
            5. Ejemplos de uso en componentes
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de integración con API")
                return {
                    'status': 'success',
                    'api_integration': result,
                    'integrated_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al integrar con API: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente programador frontend
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            'status': 'active',
            'current_task': self.current_task,
            'working_dir': str(self.working_dir)
        }