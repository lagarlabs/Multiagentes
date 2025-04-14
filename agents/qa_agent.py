"""
Agente QA del sistema multiagentes.
Este agente se encarga de revisar la calidad del código y la documentación.
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

class QAAgent:
    """Agente QA que revisa la calidad del código y documentación"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente QA
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un experto en QA con años de experiencia en revisión de código.
                Tu objetivo es asegurar que el código cumpla con los más altos estándares de calidad.
                
                Tus responsabilidades incluyen:
                1. Revisar la calidad y legibilidad del código
                2. Verificar la documentación
                3. Validar las pruebas unitarias
                4. Identificar posibles problemas y áreas de mejora
                5. Asegurar el cumplimiento de buenas prácticas
                
                Tu estilo de revisión es:
                - Minucioso y detallado
                - Constructivo y orientado a soluciones
                - Enfocado en la calidad y mantenibilidad
                - Basado en estándares y mejores prácticas\
            """),
            instructions=dedent("""\
                1. Analiza el código en busca de:
                   - Problemas de diseño
                   - Posibles bugs
                   - Deuda técnica
                   - Violaciones de principios SOLID
                
                2. Revisa la documentación verificando:
                   - Claridad y completitud
                   - Ejemplos de uso
                   - Explicación de parámetros
                   - Descripción de retornos
                
                3. Evalúa las pruebas unitarias:
                   - Cobertura de código
                   - Casos de prueba
                   - Manejo de errores
                   - Escenarios edge-case
                
                4. Genera un reporte detallado con:
                   - Evaluación general (1-5 estrellas)
                   - Lista de problemas encontrados
                   - Sugerencias de mejora
                   - Decisión final (aprobar/rechazar)\
            """),
            expected_output=dedent("""\
                {
                    "evaluation": {
                        "code_quality": 0-5,
                        "documentation": 0-5,
                        "tests": 0-5,
                        "overall": 0-5
                    },
                    "issues": [
                        {
                            "type": "code|documentation|tests",
                            "severity": "high|medium|low",
                            "description": "Descripción del problema",
                            "suggestion": "Sugerencia de mejora"
                        }
                    ],
                    "approved": true|false,
                    "summary": "Resumen general de la revisión"
                }\
            """),
            markdown=True
        )
        
        # Inicializar el agente de razonamiento con DeepSeek
        self.reasoning_agent = Agent(
            model=DeepSeekChat(id=self.config.get("reasoning_model")),
            description=dedent("""\
                Eres un experto en análisis de código que utiliza razonamiento paso a paso
                para evaluar la calidad y seguridad del código.\
            """),
            instructions=dedent("""\
                1. Analiza el código paso a paso
                2. Identifica posibles problemas de seguridad
                3. Evalúa la eficiencia algorítmica
                4. Verifica el manejo de errores
                5. Proporciona sugerencias detalladas\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.current_review = None
        logger.info("Agente QA inicializado")

    async def perform_review(self, implementation: Dict) -> Dict:
        """
        Realiza una revisión de calidad del código y documentación
        
        Args:
            implementation (Dict): Implementación a revisar
            
        Returns:
            Dict: Resultado de la revisión
        """
        try:
            # Primero usar el agente de razonamiento para un análisis profundo
            reasoning_prompt = f"""
            Analiza el siguiente código paso a paso:
            
            CÓDIGO:
            {implementation.get('code', '')}
            
            DOCUMENTACIÓN:
            {implementation.get('documentation', '')}
            
            PRUEBAS:
            {implementation.get('tests', '')}
            """
            
            reasoning_response = await self.reasoning_agent.arun(reasoning_prompt)
            
            # Usar el análisis del agente de razonamiento como parte del prompt principal
            review_prompt = f"""
            Revisa la siguiente implementación, teniendo en cuenta el análisis previo:
            
            ANÁLISIS PREVIO:
            {reasoning_response.content}
            
            CÓDIGO:
            {implementation.get('code', '')}
            
            DOCUMENTACIÓN:
            {implementation.get('documentation', '')}
            
            PRUEBAS:
            {implementation.get('tests', '')}
            
            Genera un reporte detallado siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(review_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de revisión")
                return {
                    'status': 'success',
                    'review': result,
                    'reasoning': reasoning_response.content,
                    'reviewed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error en la revisión: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def check_tests(self, tests: Dict) -> Dict:
        """
        Verifica la calidad de las pruebas
        
        Args:
            tests (Dict): Pruebas a verificar
            
        Returns:
            Dict: Resultado de la verificación
        """
        try:
            prompt = f"""
            Verifica la calidad de las siguientes pruebas:
            
            PRUEBAS:
            {tests.get('code', '')}
            
            COBERTURA:
            {tests.get('coverage', '')}
            
            Genera un reporte JSON con:
            1. Evaluación de cobertura (porcentaje)
            2. Lista de casos faltantes
            3. Sugerencias de mejora
            4. Decisión final (aprobar/rechazar)
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de verificación de pruebas")
                return {
                    'status': 'success',
                    'review': result,
                    'reviewed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error en la verificación de pruebas: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    async def check_documentation(self, documentation: Dict) -> Dict:
        """
        Verifica la calidad de la documentación
        
        Args:
            documentation (Dict): Documentación a verificar
            
        Returns:
            Dict: Resultado de la verificación
        """
        try:
            prompt = f"""
            Verifica la calidad de la siguiente documentación:
            
            DOCUMENTACIÓN:
            {documentation.get('content', '')}
            
            Genera un reporte JSON con:
            1. Evaluación de claridad (1-5 estrellas)
            2. Lista de secciones faltantes
            3. Sugerencias de mejora
            4. Decisión final (aprobar/rechazar)
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de verificación de documentación")
                return {
                    'status': 'success',
                    'review': result,
                    'reviewed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error en la verificación de documentación: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente QA
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            'status': 'active',
            'current_review': self.current_review,
            'working_dir': str(self.working_dir)
        }