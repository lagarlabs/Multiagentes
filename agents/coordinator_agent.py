"""
Agente Coordinador del sistema multiagentes.
Este agente se encarga de coordinar las tareas entre los demás agentes.
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

from .programmer_agent import ProgrammerAgent
from .qa_agent import QAAgent
from utils.json_helpers import parse_agent_response
from utils.config_manager import ConfigManager

class CoordinatorAgent:
    """Agente coordinador que gestiona las tareas entre los demás agentes"""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el agente coordinador
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        # Obtener configuración
        self.config = ConfigManager()
        
        # Inicializar el agente principal con OpenAI
        self.agent = Agent(
            model=OpenAIChat(id=self.config.get("default_model")),
            description=dedent("""\
                Eres un líder técnico experto con años de experiencia en gestión de proyectos.
                Tu objetivo es coordinar el desarrollo de software de manera eficiente.
                
                Tus responsabilidades incluyen:
                1. Analizar requerimientos del proyecto
                2. Diseñar la arquitectura del sistema
                3. Asignar tareas a los agentes
                4. Supervisar la calidad del código
                5. Asegurar la integración correcta
                
                Tu estilo de gestión es:
                - Organizado y metódico
                - Orientado a resultados
                - Enfocado en la calidad
                - Promoviendo buenas prácticas\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos del proyecto
                2. Diseña la arquitectura general
                3. Divide el trabajo en tareas manejables
                4. Asigna tareas a los agentes apropiados
                5. Supervisa el progreso y la calidad
                6. Integra los componentes del sistema\
            """),
            expected_output=dedent("""\
                {
                    "project": {
                        "name": "nombre_proyecto",
                        "description": "descripción",
                        "architecture": {
                            "components": [],
                            "interactions": []
                        },
                        "tasks": [
                            {
                                "id": "task_id",
                                "description": "descripción",
                                "assigned_to": "agent_id",
                                "dependencies": [],
                                "status": "pending|in_progress|completed"
                            }
                        ]
                    },
                    "status": {
                        "progress": 0-100,
                        "current_phase": "planning|development|testing|integration",
                        "issues": [],
                        "next_steps": []
                    }
                }\
            """),
            markdown=True
        )
        
        # Inicializar el agente de razonamiento con DeepSeek
        self.reasoning_agent = Agent(
            model=DeepSeekChat(id=self.config.get("reasoning_model")),
            description=dedent("""\
                Eres un arquitecto de software que utiliza razonamiento paso a paso
                para diseñar sistemas complejos y tomar decisiones estratégicas.\
            """),
            instructions=dedent("""\
                1. Analiza los requerimientos del sistema
                2. Identifica componentes y dependencias
                3. Evalúa opciones arquitectónicas
                4. Planifica la implementación
                5. Proporciona justificación de decisiones\
            """),
            markdown=True
        )
        
        self.working_dir = working_dir or Path.cwd()
        self.programmer = ProgrammerAgent(working_dir)
        self.qa = QAAgent(working_dir)
        self.current_project = None
        logger.info("Agente Coordinador inicializado")

    async def process_request(self, request: str) -> Dict:
        """
        Procesa una solicitud de proyecto
        
        Args:
            request (str): Descripción del proyecto
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            # Primero usar el agente de razonamiento para analizar y diseñar
            analysis_prompt = f"""
            Analiza la siguiente solicitud y diseña una solución:
            
            SOLICITUD:
            {request}
            
            Proporciona:
            1. Análisis detallado de requerimientos
            2. Arquitectura propuesta
            3. Plan de implementación
            4. Riesgos y consideraciones
            """
            
            analysis_response = await self.reasoning_agent.arun(analysis_prompt)
            
            # Usar el análisis para crear el plan del proyecto
            planning_prompt = f"""
            Crea un plan de proyecto basado en el siguiente análisis:
            
            ANÁLISIS:
            {analysis_response.content}
            
            SOLICITUD:
            {request}
            
            Genera un plan detallado siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(planning_prompt)
            
            try:
                plan = parse_agent_response(response.content, "respuesta del plan")
                self.current_project = plan
                
                # Comenzar la implementación
                for task in plan["project"]["tasks"]:
                    if task["assigned_to"] == "programmer":
                        implementation = await self.programmer.generate_implementation({
                            "description": task["description"],
                            "constraints": task.get("constraints", ""),
                            "technologies": task.get("technologies", "")
                        })
                        
                        if implementation["status"] != "success":
                            raise Exception(f"Error en implementación: {implementation['error']}")
                            
                        # Enviar a QA para revisión
                        review = await self.qa.perform_review(implementation["implementation"])
                        
                        if review["status"] != "success":
                            raise Exception(f"Error en revisión QA: {review['error']}")
                            
                        # Si QA no aprueba, refactorizar
                        if not review["review"]["approved"]:
                            refactored = await self.programmer.refactor_code(
                                implementation["implementation"],
                                review["review"]
                            )
                            
                            if refactored["status"] != "success":
                                raise Exception(f"Error en refactorización: {refactored['error']}")
                                
                            implementation = refactored
                            
                        task["implementation"] = implementation
                        task["qa_review"] = review
                        task["status"] = "completed"
                        
                return {
                    "status": "success",
                    "project": plan,
                    "processed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Error al procesar respuesta JSON: {str(e)}",
                    "raw_response": response.content
                }
                
        except Exception as e:
            logger.error(f"Error al procesar solicitud: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def update_project(self, project_id: str, updates: Dict) -> Dict:
        """
        Actualiza el estado de un proyecto
        
        Args:
            project_id (str): ID del proyecto
            updates (Dict): Actualizaciones a realizar
            
        Returns:
            Dict: Resultado de la actualización
        """
        try:
            if not self.current_project:
                raise Exception("No hay proyecto activo")
                
            prompt = f"""
            Actualiza el siguiente proyecto con los cambios proporcionados:
            
            PROYECTO ACTUAL:
            {json.dumps(self.current_project, indent=2)}
            
            ACTUALIZACIONES:
            {json.dumps(updates, indent=2)}
            
            Genera un nuevo estado del proyecto siguiendo el formato JSON especificado.
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta de actualización")
                self.current_project = result
                return {
                    "status": "success",
                    "project": result,
                    "updated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Error al procesar respuesta JSON: {str(e)}",
                    "raw_response": response.content
                }
                
        except Exception as e:
            logger.error(f"Error al actualizar proyecto: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def generate_report(self) -> Dict:
        """
        Genera un reporte del estado actual del proyecto
        
        Returns:
            Dict: Reporte generado
        """
        try:
            if not self.current_project:
                raise Exception("No hay proyecto activo")
                
            prompt = f"""
            Genera un reporte detallado del siguiente proyecto:
            
            PROYECTO:
            {json.dumps(self.current_project, indent=2)}
            
            El reporte debe incluir:
            1. Resumen ejecutivo
            2. Estado actual
            3. Progreso por componente
            4. Problemas y riesgos
            5. Próximos pasos
            
            Genera el reporte en formato JSON.
            """
            
            response = await self.agent.arun(prompt)
            
            try:
                result = parse_agent_response(response.content, "respuesta del reporte")
                return {
                    "status": "success",
                    "report": result,
                    "generated_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Error al procesar respuesta JSON: {str(e)}",
                    "raw_response": response.content
                }
                
        except Exception as e:
            logger.error(f"Error al generar reporte: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
            
    def get_status(self) -> Dict:
        """
        Obtiene el estado actual del agente coordinador
        
        Returns:
            Dict: Estado actual del agente
        """
        return {
            "status": "active",
            "current_project": self.current_project,
            "working_dir": str(self.working_dir)
        }