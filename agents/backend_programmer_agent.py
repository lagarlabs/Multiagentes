"""
Agente Programador Backend del sistema multiagentes.
Este agente se especializa en desarrollo backend.
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

class BackendProgrammerAgent:
    """Agente programador especializado en desarrollo backend"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente programador backend
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un ingeniero de software backend experto con años de experiencia.
                Tu objetivo es generar código backend de alta calidad, eficiente y escalable.
                
                Tus responsabilidades incluyen:
                1. Diseñar e implementar APIs RESTful
                2. Desarrollar la lógica de negocio
                3. Integrar con bases de datos y servicios externos
                4. Implementar autenticación y autorización
                5. Optimizar consultas y rendimiento del servidor
                
                Tu estilo de programación es:
                - Modular y mantenible
                - Eficiente y optimizado
                - Siguiendo principios SOLID
                - Seguro y robusto
                - Bien documentado y testeado\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos técnicos en detalle
                2. Diseña una arquitectura backend escalable
                3. Implementa APIs claras y consistentes
                4. Optimiza consultas a bases de datos
                5. Implementa manejo de errores robusto
                6. Documenta exhaustivamente el código
                7. Incluye pruebas unitarias\
            """),
            expected_output=dedent("""\
                {
                    "backend": {
                        "architecture": {
                            "description": "descripción de la arquitectura",
                            "components": ["componente1", "componente2"]
                        },
                        "api": {
                            "endpoints": [
                                {
                                    "path": "/ruta",
                                    "method": "GET|POST|PUT|DELETE",
                                    "description": "descripción",
                                    "request_schema": {},
                                    "response_schema": {}
                                }
                            ],
                            "authentication": "descripción de autenticación",
                            "error_handling": "descripción de manejo de errores"
                        },
                        "database": {
                            "model": "modelo de datos",
                            "schema": "esquema de base de datos",
                            "queries": "consultas optimizadas"
                        },
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
                        "api_docs": "documentación de API",
                        "examples": "ejemplos de uso"
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
                Eres un arquitecto de software backend que utiliza razonamiento paso a paso
                para diseñar sistemas robustos, escalables y eficientes.\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos paso a paso
                2. Diseña la arquitectura de datos
                3. Define las interfaces de API
                4. Planifica la escalabilidad
                5. Considera seguridad y rendimiento\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.current_task = None
        logger.info("Agente Programador Backend inicializado")

    async def design_database(self, requirements: Dict) -> Dict:
        """
        Diseña la estructura de base de datos para el proyecto
        
        Args:
            requirements (Dict): Requerimientos del proyecto
            
        Returns:
            Dict: Diseño de la base de datos
        """
        try:
            # Usar el agente de razonamiento para diseñar la base de datos
            design_prompt = f"""
            Diseña una estructura de base de datos basada en los siguientes requerimientos:
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            ENTIDADES PRINCIPALES:
            {requirements.get('entities', [])}
            
            RELACIONES:
            {requirements.get('relationships', [])}
            
            Proporciona un diseño detallado siguiendo un razonamiento paso a paso:
            1. Identificar entidades y atributos
            2. Determinar relaciones (uno a uno, uno a muchos, muchos a muchos)
            3. Normalizar hasta 3NF
            4. Definir claves primarias y foráneas
            5. Considerar índices para optimizar consultas
            """
            
            design_response = await self.reasoning_agent.arun(design_prompt)
            
            # Usar el diseño para generar el esquema detallado
            schema_prompt = f"""
            Genera un esquema de base de datos basado en el siguiente diseño:
            
            DISEÑO:
            {design_response.content}
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            Genera un esquema detallado en formato JSON que incluya:
            1. Modelos/tablas con campos y tipos de datos
            2. Relaciones entre tablas
            3. Índices recomendados
            4. Consideraciones de rendimiento
            5. Código SQL o ORM para implementar el esquema
            """
            
            response = await self.agent.arun(schema_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de diseño de base de datos")
                return {
                    'status': 'success',
                    'database_design': result,
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
            logger.error(f"Error al diseñar base de datos: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def implement_api(self, requirements: Dict, database_design: Dict) -> Dict:
        """
        Implementa una API basada en los requerimientos y el diseño de base de datos
        
        Args:
            requirements (Dict): Requerimientos del proyecto
            database_design (Dict): Diseño de la base de datos
            
        Returns:
            Dict: Implementación de la API
        """
        try:
            # Usar el agente de razonamiento para diseñar la API
            api_design_prompt = f"""
            Diseña una API basada en los siguientes requerimientos y diseño de base de datos:
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            DISEÑO DE BASE DE DATOS:
            {json.dumps(database_design, indent=2)}
            
            FUNCIONALIDADES REQUERIDAS:
            {requirements.get('features', [])}
            
            Proporciona un diseño detallado de API siguiendo un razonamiento paso a paso:
            1. Identificar recursos principales
            2. Definir endpoints para cada recurso (GET, POST, PUT, DELETE)
            3. Diseñar estructura de respuestas y códigos de estado
            4. Planificar autenticación y autorización
            5. Considerar rate limiting y caché
            """
            
            api_design_response = await self.reasoning_agent.arun(api_design_prompt)
            
            # Usar el diseño para implementar la API
            implementation_prompt = f"""
            Implementa una API basada en el siguiente diseño:
            
            DISEÑO DE API:
            {api_design_response.content}
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            DISEÑO DE BASE DE DATOS:
            {json.dumps(database_design, indent=2)}
            
            Genera una implementación completa siguiendo el formato JSON especificado.
            Incluye:
            1. Definición de endpoints
            2. Código de implementación
            3. Esquemas de datos
            4. Documentación de la API
            5. Tests para los endpoints principales
            """
            
            response = await self.agent.arun(implementation_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de implementación de API")
                return {
                    'status': 'success',
                    'api_implementation': result,
                    'design': api_design_response.content,
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
            logger.error(f"Error al implementar API: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def implement_business_logic(self, requirements: Dict, api_design: Dict) -> Dict:
        """
        Implementa la lógica de negocio
        
        Args:
            requirements (Dict): Requerimientos del proyecto
            api_design (Dict): Diseño de la API
            
        Returns:
            Dict: Implementación de la lógica de negocio
        """
        try:
            prompt = f"""
            Implementa la lógica de negocio basada en los siguientes requerimientos y diseño de API:
            
            REQUERIMIENTOS:
            {requirements.get('description', '')}
            
            DISEÑO DE API:
            {json.dumps(api_design, indent=2)}
            
            REGLAS DE NEGOCIO:
            {requirements.get('business_rules', [])}
            
            Genera una implementación completa siguiendo el formato JSON especificado.
            Incluye:
            1. Servicios y controladores
            2. Gestión de estados y transiciones
            3. Validaciones y reglas de negocio
            4. Manejo de errores y excepciones
            5. Tests unitarios
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de lógica de negocio")
                return {
                    'status': 'success',
                    'business_logic': result,
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
            logger.error(f"Error al implementar lógica de negocio: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente programador backend
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            'status': 'active',
            'current_task': self.current_task,
            'working_dir': str(self.working_dir)
        }