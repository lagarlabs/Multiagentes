"""
Agente de Análisis de Mercado del sistema multiagentes.
Este agente se encarga de analizar tendencias del mercado y asegurar que el proyecto sea competitivo.
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

class MarketAnalysisAgent:
    """Agente de análisis de mercado que evalúa tendencias y competitividad del proyecto"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente de análisis de mercado
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un analista de mercado experto con años de experiencia en tendencias tecnológicas.
                Tu objetivo es evaluar proyectos de software y asegurar que sean competitivos en el mercado.
                
                Tus responsabilidades incluyen:
                1. Analizar tendencias actuales del mercado
                2. Evaluar competidores y soluciones similares
                3. Identificar oportunidades de diferenciación
                4. Recomendar mejoras para aumentar competitividad
                5. Analizar el potencial de monetización
                
                Tu estilo de análisis es:
                - Objetivo y basado en datos
                - Orientado a resultados prácticos
                - Estratégico y con visión a futuro
                - Enfocado en necesidades del mercado real\
            """),
            instructions=dedent("""\
                1. Analiza las tendencias actuales del mercado
                2. Identifica competidores clave y sus fortalezas/debilidades
                3. Evalúa el potencial de monetización
                4. Identifica oportunidades de diferenciación
                5. Recomienda mejoras específicas para aumentar competitividad
                6. Proporciona métricas y KPIs para medir éxito\
            """),
            expected_output=dedent("""\
                {
                    "market_analysis": {
                        "trends": [
                            {
                                "name": "nombre_tendencia",
                                "relevance": 1-10,
                                "description": "descripción"
                            }
                        ],
                        "competitors": [
                            {
                                "name": "nombre_competidor",
                                "strengths": ["fortaleza1", "fortaleza2"],
                                "weaknesses": ["debilidad1", "debilidad2"],
                                "market_share": "estimación"
                            }
                        ],
                        "monetization": {
                            "potential": 1-10,
                            "models": ["modelo1", "modelo2"],
                            "estimated_revenue": "estimación"
                        }
                    },
                    "recommendations": [
                        {
                            "area": "área_de_mejora",
                            "description": "descripción",
                            "priority": "alta|media|baja",
                            "impact": 1-10
                        }
                    ],
                    "competitive_advantage": {
                        "score": 1-10,
                        "strengths": ["fortaleza1", "fortaleza2"],
                        "opportunities": ["oportunidad1", "oportunidad2"]
                    },
                    "kpis": [
                        {
                            "name": "nombre_kpi",
                            "description": "descripción",
                            "target": "objetivo",
                            "measurement": "forma_de_medir"
                        }
                    ]
                }\
            """),
            markdown=True
        )
        
        # Inicializar el agente de razonamiento con DeepSeek
        self.reasoning_agent = Agent(
            model=DeepSeekChat(id=self.config.get("reasoning_model")),
            description=dedent("""\
                Eres un estratega de mercado que utiliza razonamiento paso a paso
                para analizar tendencias tecnológicas y oportunidades de negocio.\
            """),
            instructions=dedent("""\
                1. Analiza el sector tecnológico actual
                2. Identifica tendencias emergentes y su potencial
                3. Evalúa el posicionamiento estratégico
                4. Analiza la propuesta de valor del proyecto
                5. Proporciona estrategias concretas de diferenciación\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.current_analysis = None
        logger.info("Agente de Análisis de Mercado inicializado")

    async def analyze_market_fit(self, project_details: Dict) -> Dict:
        """
        Analiza el ajuste del proyecto al mercado actual
        
        Args:
            project_details (Dict): Detalles del proyecto a analizar
            
        Returns:
            Dict: Resultado del análisis
        """
        try:
            # Primero usar el agente de razonamiento para análisis profundo
            reasoning_prompt = f"""
            Analiza el ajuste del siguiente proyecto al mercado actual:
            
            DESCRIPCIÓN DEL PROYECTO:
            {project_details.get('description', '')}
            
            TECNOLOGÍAS:
            {project_details.get('technologies', [])}
            
            CARACTERÍSTICAS PRINCIPALES:
            {project_details.get('features', [])}
            
            Proporciona un análisis detallado siguiendo un razonamiento paso a paso.
            """
            
            reasoning_response = await self.reasoning_agent.arun(reasoning_prompt)
            
            # Usar el análisis para generar el informe de mercado
            market_prompt = f"""
            Basado en el siguiente análisis, evalúa el ajuste al mercado del proyecto:
            
            ANÁLISIS PRELIMINAR:
            {reasoning_response.content}
            
            DESCRIPCIÓN DEL PROYECTO:
            {project_details.get('description', '')}
            
            TECNOLOGÍAS:
            {project_details.get('technologies', [])}
            
            CARACTERÍSTICAS PRINCIPALES:
            {project_details.get('features', [])}
            
            Genera un análisis completo siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(market_prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de análisis de mercado")
                self.current_analysis = result
                return {
                    'status': 'success',
                    'analysis': result,
                    'reasoning': reasoning_response.content,
                    'analyzed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al analizar ajuste al mercado: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def recommend_improvements(self, project_details: Dict, market_analysis: Dict) -> Dict:
        """
        Recomienda mejoras para aumentar la competitividad del proyecto
        
        Args:
            project_details (Dict): Detalles del proyecto
            market_analysis (Dict): Análisis de mercado previo
            
        Returns:
            Dict: Recomendaciones para mejorar competitividad
        """
        try:
            prompt = f"""
            Basado en el análisis de mercado y el estado actual del proyecto, 
            recomienda mejoras específicas para aumentar su competitividad:
            
            ANÁLISIS DE MERCADO:
            {json.dumps(market_analysis, indent=2)}
            
            ESTADO ACTUAL DEL PROYECTO:
            {json.dumps(project_details, indent=2)}
            
            Genera recomendaciones detalladas siguiendo el formato JSON especificado.
            Enfócate en:
            1. Características diferenciadoras a añadir
            2. Tecnologías a incorporar o actualizar
            3. Posicionamiento estratégico
            4. Oportunidades de monetización
            5. Mejoras en UX/UI
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de recomendaciones")
                return {
                    'status': 'success',
                    'recommendations': result,
                    'recommended_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al generar recomendaciones: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

    async def analyze_competitors(self, sector: str, project_type: str) -> Dict:
        """
        Analiza competidores en un sector específico
        
        Args:
            sector (str): Sector tecnológico
            project_type (str): Tipo de proyecto
            
        Returns:
            Dict: Análisis de competidores
        """
        try:
            prompt = f"""
            Realiza un análisis de competidores para un proyecto de tipo:
            
            SECTOR: {sector}
            TIPO DE PROYECTO: {project_type}
            
            Incluye:
            1. Principales competidores
            2. Cuota de mercado estimada
            3. Fortalezas y debilidades de cada uno
            4. Oportunidades de diferenciación
            5. Amenazas a considerar
            
            Genera un análisis detallado siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de análisis de competidores")
                return {
                    'status': 'success',
                    'competitors_analysis': result,
                    'analyzed_at': datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    'status': 'error',
                    'error': f"Error al procesar respuesta JSON: {str(e)}",
                    'raw_response': response.content
                }
                
        except Exception as e:
            logger.error(f"Error al analizar competidores: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente de análisis de mercado
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            'status': 'active',
            'current_analysis': self.current_analysis,
            'working_dir': str(self.working_dir)
        }