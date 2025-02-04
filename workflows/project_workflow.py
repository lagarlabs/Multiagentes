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

class ProjectWorkflow(Workflow):
    """
    Workflow para gestionar el desarrollo de proyectos usando múltiples agentes
    """
    
    def __init__(self):
        """Inicializa el workflow con configuración de modelos"""
        super().__init__()
        
        # Verificar configuración
        logging.info("Inicializando ProjectWorkflow...")
        logging.info(f"DEFAULT_MODEL: {os.getenv('DEFAULT_MODEL')}")
        logging.info(f"OPENAI_API_KEY presente: {bool(os.getenv('OPENAI_API_KEY'))}")
        
        try:
            # Configurar modelo principal
            self.openai_model = OpenAIChat(
                id="gpt-4o",  # Usar gpt-4o
                temperature=float(os.getenv("TEMPERATURE", "0.7")),
                max_tokens=int(os.getenv("MAX_TOKENS", "2000")),
                max_retries=int(os.getenv("MAX_RETRIES", "3")),
                api_key=os.getenv("OPENAI_API_KEY")  # Agregar explícitamente la API key
            )
            logging.info("Modelo OpenAI inicializado correctamente")
            
        except Exception as e:
            logging.error(f"Error al inicializar modelo OpenAI: {str(e)}")
            raise
        
        # Inicializar base de conocimiento
        self.knowledge_base = self.setup_knowledge_base()
        
        # Configurar agentes
        self.setup_agents()
    
    def setup_knowledge_base(self):
        """Configura la base de conocimiento para los agentes"""
        return AgentKnowledge(
            vector_db=PgVector(
                table_name="project_knowledge",
                db_url=os.getenv("DATABASE_URL", "postgresql://localhost:5432/agno"),
                search_type="hybrid"
            )
        )
    
    def setup_agents(self):
        """Configura los agentes especializados"""
        
        # Verificar configuración de GitHub
        github_token = os.getenv("GITHUB_TOKEN")
        logging.info(f"GitHub Token presente: {bool(github_token)}")
        if not github_token:
            logging.error("GitHub Token no encontrado en variables de entorno")
            raise ValueError("GitHub access token is required")
        
        # Herramientas comunes
        try:
            github_tools = GithubTools(github_token)  # Solo usar el token
            logging.info("GithubTools inicializado correctamente")
        except Exception as e:
            logging.error(f"Error al inicializar GithubTools: {str(e)}")
            raise
            
        shell_tools = ShellTools()
        duck_tools = DuckDuckGoTools()
        firecrawl_tools = FirecrawlTools()
        
        # Investigador y Analista
        self.research_agent = Agent(
            name="Research Specialist",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[duck_tools, firecrawl_tools, shell_tools],
            description="""Eres un investigador experto en tecnologías y desarrollo de software.
            Tienes la capacidad de ejecutar comandos en la terminal y crear archivos cuando sea necesario.
            Tu especialidad es analizar requisitos técnicos y proponer soluciones óptimas.""",
            instructions=[
                "Investiga a fondo las tecnologías solicitadas",
                "Analiza las mejores prácticas actuales",
                "Evalúa ventajas y desventajas de cada opción",
                "Crea archivos de documentación cuando sea necesario",
                "Ejecuta comandos para instalar dependencias requeridas",
                "IMPORTANTE: Responde SOLO con el JSON especificado"
            ],
            expected_output="""{
                "technologies": ["lista", "de", "tecnologías"],
                "best_practices": ["lista", "de", "mejores", "prácticas"],
                "considerations": ["lista", "de", "consideraciones"],
                "examples": ["lista", "de", "ejemplos"],
                "actions_taken": ["lista", "de", "acciones", "ejecutadas"]
            }""",
            markdown=True,
            show_tool_calls=True
        )
        
        # Arquitecto
        self.architect = Agent(
            name="Solution Architect",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[github_tools, shell_tools],
            description="""Eres un arquitecto de software experto con capacidad de ejecutar comandos y crear archivos.
            Tu objetivo es diseñar soluciones técnicas robustas y crear la estructura base del proyecto.""",
            instructions=[
                "Diseña arquitecturas modulares y mantenibles",
                "Crea la estructura inicial de directorios",
                "Inicializa archivos de configuración",
                "Configura el entorno de desarrollo",
                "Ejecuta comandos para preparar el proyecto",
                "IMPORTANTE: Responde SOLO con el JSON especificado"
            ],
            expected_output="""{
                "components": ["lista", "de", "componentes"],
                "patterns": ["lista", "de", "patrones"],
                "security": ["consideraciones", "de", "seguridad"],
                "architecture": {
                    "descripción": "de la arquitectura",
                    "diagrama": "descripción textual del diagrama"
                },
                "actions_taken": ["lista", "de", "acciones", "ejecutadas"]
            }""",
            markdown=True,
            show_tool_calls=True
        )
        
        # Desarrollador
        self.developer = Agent(
            name="Lead Developer",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[github_tools, shell_tools],
            description="""Eres un desarrollador senior con capacidad de ejecutar comandos y crear/modificar archivos.
            Tu objetivo es implementar código de alta calidad y gestionar el proyecto.""",
            instructions=[
                "Crea y modifica archivos de código",
                "Implementa las funcionalidades requeridas",
                "Ejecuta pruebas y verifica la calidad",
                "Gestiona dependencias del proyecto",
                "Usa la terminal para tareas de desarrollo",
                "IMPORTANTE: Responde SOLO con el JSON especificado"
            ],
            expected_output="""{
                "title": "Título del proyecto",
                "description": "Descripción detallada",
                "tasks": [
                    {
                        "id": "task-1",
                        "title": "Título de la tarea",
                        "description": "Descripción detallada",
                        "estimated_hours": 4.5,
                        "dependencies": ["lista", "de", "ids"],
                        "status": "pending",
                        "files_created": ["lista", "de", "archivos"],
                        "commands_executed": ["lista", "de", "comandos"]
                    }
                ],
                "total_estimated_hours": 10.5,
                "technologies": ["tech1", "tech2"],
                "requirements": ["req1", "req2"],
                "architecture": {"key": "value"},
                "security_considerations": ["sec1", "sec2"],
                "actions_taken": ["lista", "de", "acciones", "ejecutadas"]
            }""",
            markdown=True,
            show_tool_calls=True
        )
        
        # QA y Tester
        self.qa_agent = Agent(
            name="Quality Assurance",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[shell_tools],
            description="""Eres un experto en control de calidad y testing.
            Tu objetivo es garantizar la calidad y confiabilidad del software.""",
            instructions=[
                "Revisa el código exhaustivamente",
                "Ejecuta y verifica pruebas unitarias",
                "Realiza pruebas de integración",
                "Identifica posibles problemas de seguridad",
                "Sugiere mejoras y optimizaciones"
            ],
            markdown=True,
            show_tool_calls=True
        )
        
        # DevOps Engineer
        self.devops_agent = Agent(
            name="DevOps Engineer",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[shell_tools, github_tools],
            description="""Eres un ingeniero DevOps experimentado.
            Te especializas en automatización, CI/CD y despliegue.""",
            instructions=[
                "Configura entornos de desarrollo",
                "Implementa pipelines de CI/CD",
                "Gestiona dependencias y paquetes",
                "Optimiza procesos de build y deploy",
                "Monitorea el rendimiento del sistema"
            ],
            markdown=True,
            show_tool_calls=True
        )
        
        # Security Expert
        self.security_agent = Agent(
            name="Security Expert",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[github_tools, shell_tools],
            description="""Eres un experto en seguridad de aplicaciones.
            Tu misión es identificar y prevenir vulnerabilidades.""",
            instructions=[
                "Realiza análisis de seguridad",
                "Identifica vulnerabilidades potenciales",
                "Recomienda mejores prácticas de seguridad",
                "Audita el código en busca de problemas",
                "Propone soluciones de seguridad"
            ],
            markdown=True,
            show_tool_calls=True
        )

    async def process_agent_actions(self, actions: List[str], cwd: str) -> None:
        """
        Procesa las acciones ejecutadas por un agente
        
        Args:
            actions: Lista de acciones a ejecutar
            cwd: Directorio de trabajo
        """
        for action in actions:
            try:
                if action.startswith("create_file:"):
                    # Formato: create_file:path:content
                    _, path, content = action.split(":", 2)
                    full_path = os.path.join(cwd, path.replace("/", "\\"))
                    os.makedirs(os.path.dirname(full_path), exist_ok=True)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    logging.info(f"Archivo creado: {full_path}")
                
                elif action.startswith("run_command:"):
                    # Formato: run_command:command
                    command = action.split(":", 1)[1]
                    logging.info(f"Ejecutando comando: {command}")
                    
                    # Convertir comandos Unix a Windows
                    if command.startswith("mkdir"):
                        parts = command.split()
                        if "-p" in parts:
                            parts.remove("-p")
                        dirs = [p.replace("/", "\\") for p in parts[1:]]
                        for dir_path in dirs:
                            full_path = os.path.join(cwd, dir_path)
                            os.makedirs(full_path, exist_ok=True)
                            logging.info(f"Directorio creado: {full_path}")
                    
                    elif command.startswith("touch"):
                        # Convertir touch a crear archivo vacío
                        parts = command.split()
                        file_path = parts[1].replace("/", "\\")
                        full_path = os.path.join(cwd, file_path)
                        os.makedirs(os.path.dirname(full_path), exist_ok=True)
                        open(full_path, 'a').close()
                        logging.info(f"Archivo creado: {full_path}")
                    
                    elif command.startswith("npm"):
                        # Usar npm desde cmd
                        modified_command = f"cmd /c {command}"
                        process = await asyncio.create_subprocess_shell(
                            modified_command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=cwd
                        )
                        stdout, stderr = await process.communicate()
                        if stdout:
                            logging.info(f"Salida: {stdout.decode()}")
                        if stderr:
                            logging.error(f"Error: {stderr.decode()}")
                    
                    else:
                        process = await asyncio.create_subprocess_shell(
                            command,
                            stdout=asyncio.subprocess.PIPE,
                            stderr=asyncio.subprocess.PIPE,
                            cwd=cwd
                        )
                        stdout, stderr = await process.communicate()
                        if stdout:
                            logging.info(f"Salida: {stdout.decode()}")
                        if stderr:
                            logging.error(f"Error: {stderr.decode()}")
                    
                elif action.startswith("mkdir:"):
                    # Formato: mkdir:path
                    path = action.split(":", 1)[1]
                    full_path = os.path.join(cwd, path.replace("/", "\\"))
                    os.makedirs(full_path, exist_ok=True)
                    logging.info(f"Directorio creado: {full_path}")
                
                else:
                    logging.info(f"Acción ejecutada: {action}")
                    
            except Exception as e:
                logging.error(f"Error al procesar acción {action}: {str(e)}")

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
                run_command:cmd /c comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Research response: {research_response.content}")
            
            try:
                # Limpiar la respuesta de cualquier texto adicional
                json_str = research_response.content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].strip()
                
                research_data = json.loads(json_str)
                logging.info(f"Research data parsed: {json.dumps(research_data, indent=2)}")
                
                # Procesar acciones del investigador
                if "actions_taken" in research_data:
                    await self.process_agent_actions(research_data["actions_taken"], os.getcwd())
                
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear research response: {str(e)}")
                logging.error(f"Research content: {research_response.content}")
                raise ValueError("La respuesta del investigador no es un JSON válido")
            
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
                run_command:cmd /c comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Architecture response: {architecture_response.content}")
            
            try:
                # Limpiar la respuesta de cualquier texto adicional
                json_str = architecture_response.content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].strip()
                
                architecture_data = json.loads(json_str)
                logging.info(f"Architecture data parsed: {json.dumps(architecture_data, indent=2)}")
                
                # Procesar acciones del arquitecto
                if "actions_taken" in architecture_data:
                    await self.process_agent_actions(architecture_data["actions_taken"], os.getcwd())
                
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear architecture response: {str(e)}")
                logging.error(f"Architecture content: {architecture_response.content}")
                raise ValueError("La respuesta del arquitecto no es un JSON válido")
            
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
                run_command:cmd /c comando
                
                IMPORTANTE: Responde SOLO con un objeto JSON válido según el formato especificado.
                NO incluyas ningún otro texto o explicación fuera del JSON.
                """
            )
            
            logging.info(f"Plan response: {plan_response.content}")
            
            try:
                # Limpiar la respuesta de cualquier texto adicional
                json_str = plan_response.content.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].strip()
                
                plan_dict = json.loads(json_str)
                logging.info(f"Plan data parsed: {json.dumps(plan_dict, indent=2)}")
                
                # Procesar acciones del desarrollador
                if "actions_taken" in plan_dict:
                    await self.process_agent_actions(plan_dict["actions_taken"], os.getcwd())
                
                # Procesar acciones de las tareas
                for task in plan_dict.get("tasks", []):
                    if "files_created" in task:
                        await self.process_agent_actions(task["files_created"], os.getcwd())
                    if "commands_executed" in task:
                        await self.process_agent_actions(task["commands_executed"], os.getcwd())
                
            except json.JSONDecodeError as e:
                logging.error(f"Error al parsear plan response: {str(e)}")
                logging.error(f"Plan content: {plan_response.content}")
                raise ValueError("El plan generado no es un JSON válido")
            
            # Validar que tenga todos los campos requeridos
            required_fields = ["title", "description", "tasks", "total_estimated_hours", 
                             "technologies", "requirements"]
            for field in required_fields:
                if field not in plan_dict:
                    raise ValueError(f"Campo requerido '{field}' no encontrado en el plan")
            
            # Validar que cada tarea tenga los campos requeridos
            task_fields = ["id", "title", "description", "estimated_hours"]
            for task in plan_dict["tasks"]:
                for field in task_fields:
                    if field not in task:
                        raise ValueError(f"Campo requerido '{field}' no encontrado en tarea")
            
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
            return {
                "status": "error",
                "error": str(e),
                "message": "Error al preparar el despliegue"
            }
