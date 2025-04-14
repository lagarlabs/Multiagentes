"""
Este workflow coordina los diferentes agentes para el desarrollo de software.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List
from pydantic import BaseModel, Field
from datetime import datetime
from pathlib import Path
import tempfile

from agno.workflow import Workflow
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from agno.knowledge import AgentKnowledge
from agno.tools.github import GithubTools
from agno.tools.shell import ShellTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.firecrawl import FirecrawlTools

from .models import ProjectPlan, ProjectTask
from utils.json_helpers import parse_agent_response, validate_required_fields
from utils.command_executor import process_agent_actions
from utils.config_manager import ConfigManager
from agents.agent_factory import AgentFactory

class ProjectWorkflow(Workflow):
    """
    Workflow para gestionar el desarrollo de proyectos usando múltiples agentes
    """
    
    def __init__(self):
        """Inicializa el workflow con configuración de modelos"""
        super().__init__()
        
        # Inicializar configuración
        self.config = ConfigManager()
        logging.info("Inicializando ProjectWorkflow...")
        logging.info(f"DEFAULT_MODEL: {self.config.get('default_model')}")
        logging.info(f"OPENAI_API_KEY presente: {bool(self.config.get('openai_api_key'))}")
        
        # Inicializar base de conocimiento
        self.knowledge_base = self.setup_knowledge_base()
        
        # Configurar fábrica de agentes
        self.agent_factory = AgentFactory(self.knowledge_base)
        
        # Inicializar agentes
        self.setup_agents()
        
        logging.info("ProjectWorkflow inicializado correctamente")
    
    def setup_knowledge_base(self):
        """Configura la base de conocimiento para los agentes"""
        return AgentKnowledge(
            vector_db=PgVector(
                table_name="project_knowledge",
                db_url=self.config.get("database_url"),
                search_type="hybrid"
            )
        )
    
    def setup_agents(self):
        """Configura los agentes especializados"""
        try:
            # Crear los agentes utilizando la fábrica
            self.research_agent = self.agent_factory.create_research_agent()
            self.architect = self.agent_factory.create_architect_agent()
            self.developer = self.agent_factory.create_developer_agent()
            self.qa_agent = self.agent_factory.create_qa_agent()
            self.security_agent = self.agent_factory.create_security_agent()
            self.devops_agent = self.agent_factory.create_devops_agent()
            
            logging.info("Todos los agentes inicializados correctamente")
        except Exception as e:
            logging.error(f"Error al inicializar agentes: {str(e)}")
            raise
    
    def _serialize_plan(self, plan: ProjectPlan) -> dict:
        """
        Serializa el plan a un diccionario JSON-serializable
        
        Args:
            plan: Instancia de ProjectPlan
            
        Returns:
            Dict serializable a JSON
        """
        plan_dict = plan.dict()
        
        # Convertir datetime a strings ISO
        for field in ["start_date", "created_at", "updated_at"]:
            if field in plan_dict and plan_dict[field]:
                plan_dict[field] = plan_dict[field].isoformat()
        
        return plan_dict

    async def create_project_plan(self, user_request: str) -> Dict:
        """
        Crea un plan de proyecto basado en la solicitud del usuario
        
        Args:
            user_request: Descripción del proyecto por el usuario
            
        Returns:
            Dict con el plan del proyecto y estado
        """
        try:
            # El investigador analiza requisitos y tecnologías
            research_response = await self.research_agent.arun(
                f"""
                Analiza los siguientes requisitos de proyecto:
                {user_request}
                
                Genera un análisis detallado que incluya tecnologías recomendadas,
                mejores prácticas, consideraciones técnicas y ejemplos similares.
                
                Puedes ejecutar acciones usando estos formatos:
                - create_file:ruta\\archivo:contenido (usa \\ para rutas en Windows)
                - run_command:comando (para ejecutar comandos)
                - mkdir:ruta (para crear directorios, usa \\ para rutas en Windows)
                
                Para crear archivos vacíos usa:
                create_file:ruta\\archivo:
                
                Para instalar dependencias usa:
                run_command:comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Research response: {research_response.content}")
            
            try:
                # Usar la utilidad para parsear la respuesta JSON
                research_data = parse_agent_response(
                    research_response.content, 
                    "respuesta del investigador"
                )
                logging.info(f"Research data parsed: {json.dumps(research_data, indent=2)}")
                
                # Procesar acciones del investigador
                if "actions_taken" in research_data:
                    await process_agent_actions(research_data["actions_taken"], os.getcwd())
                
            except ValueError as e:
                logging.error(f"Error al procesar respuesta del investigador: {str(e)}")
                raise ValueError(f"Error al procesar respuesta del investigador: {str(e)}")
            
            # El arquitecto diseña la solución
            architecture_response = await self.architect.arun(
                f"""
                Basado en el análisis del investigador:
                {json.dumps(research_data, indent=2)}
                
                Y los requisitos originales:
                {user_request}
                
                Diseña una arquitectura detallada para el sistema.
                
                Puedes ejecutar acciones usando estos formatos:
                - create_file:ruta\\archivo:contenido (usa \\ para rutas en Windows)
                - run_command:comando (para ejecutar comandos)
                - mkdir:ruta (para crear directorios, usa \\ para rutas en Windows)
                
                Para crear archivos vacíos usa:
                create_file:ruta\\archivo:
                
                Para instalar dependencias usa:
                run_command:comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Architecture response: {architecture_response.content}")
            
            try:
                # Usar la utilidad para parsear la respuesta JSON
                architecture_data = parse_agent_response(
                    architecture_response.content, 
                    "respuesta del arquitecto"
                )
                logging.info(f"Architecture data parsed: {json.dumps(architecture_data, indent=2)}")
                
                # Procesar acciones del arquitecto
                if "actions_taken" in architecture_data:
                    await process_agent_actions(architecture_data["actions_taken"], os.getcwd())
                
            except ValueError as e:
                logging.error(f"Error al procesar respuesta del arquitecto: {str(e)}")
                raise ValueError(f"Error al procesar respuesta del arquitecto: {str(e)}")
            
            # El planificador crea el plan detallado
            plan_response = await self.developer.arun(
                f"""
                Basado en:
                - Análisis: {json.dumps(research_data, indent=2)}
                - Arquitectura: {json.dumps(architecture_data, indent=2)}
                - Requisitos: {user_request}
                
                Crea un plan detallado para el proyecto e implementa las primeras tareas.
                
                Puedes ejecutar acciones usando estos formatos:
                - create_file:ruta\\archivo:contenido (usa \\ para rutas en Windows)
                - run_command:comando (para ejecutar comandos)
                - mkdir:ruta (para crear directorios, usa \\ para rutas en Windows)
                
                Para crear archivos vacíos usa:
                create_file:ruta\\archivo:
                
                Para instalar dependencias usa:
                run_command:comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Plan response: {plan_response.content}")
            
            try:
                # Usar la utilidad para parsear la respuesta JSON
                plan_dict = parse_agent_response(
                    plan_response.content, 
                    "respuesta del planificador"
                )
                logging.info(f"Plan data parsed: {json.dumps(plan_dict, indent=2)}")
                
                # Procesar acciones del desarrollador
                if "actions_taken" in plan_dict:
                    await process_agent_actions(plan_dict["actions_taken"], os.getcwd())
                
                # Procesar acciones de las tareas
                for task in plan_dict.get("tasks", []):
                    if "files_created" in task:
                        await process_agent_actions(task["files_created"], os.getcwd())
                    if "commands_executed" in task:
                        await process_agent_actions(task["commands_executed"], os.getcwd())
                
            except ValueError as e:
                logging.error(f"Error al procesar respuesta del planificador: {str(e)}")
                raise ValueError(f"Error al procesar respuesta del planificador: {str(e)}")
            
            # Validar que tenga todos los campos requeridos
            required_fields = ["title", "description", "tasks", "total_estimated_hours", 
                             "technologies", "requirements"]
            validate_required_fields(plan_dict, required_fields, "plan")
            
            # Validar que cada tarea tenga los campos requeridos
            task_fields = ["id", "title", "description", "estimated_hours"]
            for task in plan_dict["tasks"]:
                validate_required_fields(task, task_fields, "tarea")
            
            # Crear instancia de ProjectPlan
            plan = ProjectPlan(**plan_dict)
            
            return {
                "status": "success",
                "plan": self._serialize_plan(plan),
                "research": json.dumps(research_data, indent=2),
                "architecture": json.dumps(architecture_data, indent=2),
                "security": plan_dict.get("security_considerations", [])
            }
            
        except Exception as e:
            logging.error(f"Error al crear plan: {str(e)}")
            return {"status": "error", "error": f"Error al crear plan: {str(e)}"}

    async def implement_task(self, task: ProjectTask) -> Dict:
        """
        Implementa una tarea del proyecto
        
        Args:
            task: Tarea a implementar
            
        Returns:
            Dict con el resultado de la implementación
        """
        try:
            # El desarrollador implementa el código
            implementation = await self.developer.arun(
                f"""
                Implementa la siguiente tarea:
                
                {json.dumps(task.dict(), indent=2)}
                
                Asegúrate de:
                1. Seguir las mejores prácticas
                2. Escribir código limpio y eficiente
                3. Incluir documentación en español
                4. Crear pruebas unitarias
                5. Manejar errores apropiadamente
                """
            )
            
            logging.info(f"Implementation response: {implementation.content}")
            
            # QA revisa la implementación
            qa_review = await self.qa_agent.arun(
                f"""
                Revisa la siguiente implementación:
                
                {implementation.content}
                
                Verifica:
                1. Calidad del código
                2. Cobertura de pruebas
                3. Manejo de errores
                4. Documentación
                5. Posibles problemas
                """
            )
            
            logging.info(f"QA review response: {qa_review.content}")
            
            # El experto en seguridad audita el código
            security_review = await self.security_agent.arun(
                f"""
                Audita el siguiente código:
                
                {implementation.content}
                
                Busca:
                1. Vulnerabilidades de seguridad
                2. Malas prácticas
                3. Problemas potenciales
                4. Mejoras necesarias
                """
            )
            
            logging.info(f"Security review response: {security_review.content}")
            
            # Actualizar la tarea con la implementación
            task.code = implementation.content
            task.review_comments = [
                f"QA Review:\n{qa_review.content}",
                f"Security Review:\n{security_review.content}"
            ]
            
            return {
                "status": "success",
                "task": task.dict(),
                "implementation": implementation.content,
                "qa_review": qa_review.content,
                "security_review": security_review.content,
                "message": "Tarea implementada exitosamente"
            }
            
        except Exception as e:
            logging.error(f"Error al implementar tarea: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error al implementar la tarea"
            }

    async def deploy_project(self, project_plan: ProjectPlan) -> Dict:
        """
        Despliega el proyecto
        
        Args:
            project_plan: Plan del proyecto a desplegar
            
        Returns:
            Dict con el resultado del despliegue
        """
        try:
            # DevOps prepara el despliegue
            deployment_plan = await self.devops_agent.arun(
                f"""
                Prepara el despliegue del siguiente proyecto:
                
                {json.dumps(self._serialize_plan(project_plan), indent=2)}
                
                Considera:
                1. Configuración del entorno
                2. Dependencias necesarias
                3. Scripts de despliegue
                4. Monitoreo y logs
                5. Rollback plan
                """
            )
            
            logging.info(f"Deployment plan response: {deployment_plan.content}")
            
            # QA verifica el despliegue
            qa_verification = await self.qa_agent.arun(
                f"""
                Verifica el plan de despliegue:
                
                {deployment_plan.content}
                
                Asegura:
                1. Pruebas de integración
                2. Verificación de dependencias
                3. Pruebas de carga
                4. Monitoreo de errores
                """
            )
            
            logging.info(f"QA verification response: {qa_verification.content}")
            
            # Security verifica la seguridad
            security_verification = await self.security_agent.arun(
                f"""
                Verifica la seguridad del despliegue:
                
                {deployment_plan.content}
                
                Revisa:
                1. Configuraciones de seguridad
                2. Accesos y permisos
                3. Protección de datos
                4. Monitoreo de seguridad
                """
            )
            
            logging.info(f"Security verification response: {security_verification.content}")
            
            return {
                "status": "success",
                "deployment_plan": deployment_plan.content,
                "qa_verification": qa_verification.content,
                "security_verification": security_verification.content,
                "message": "Proyecto listo para despliegue"
            }
            
        except Exception as e:
            logging.error(f"Error al preparar el despliegue: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Error al preparar el despliegue"
            }