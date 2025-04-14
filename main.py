"""
Sistema Multi-Agentes para Desarrollo de Software.
Este módulo implementa el sistema principal que coordina los agentes usando Agno.
"""

import os
import asyncio
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv
from datetime import datetime
import json
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Confirm

from workflows.project_workflow import ProjectWorkflow, ProjectPlan, ProjectTask

# Cargar variables de entorno
load_dotenv()

# Verificar variables de entorno críticas
logger.info("Verificando variables de entorno...")
logger.info(f"OPENAI_API_KEY presente: {bool(os.getenv('OPENAI_API_KEY'))}")
logger.info(f"EXA_API_KEY presente: {bool(os.getenv('EXA_API_KEY'))}")
logger.info(f"DEFAULT_MODEL: {os.getenv('DEFAULT_MODEL')}")
logger.info(f"TEMPERATURE: {os.getenv('TEMPERATURE')}")
logger.info(f"GITHUB_TOKEN presente: {bool(os.getenv('GITHUB_TOKEN'))}")

if not os.getenv('GITHUB_TOKEN'):
    logger.error("GITHUB_TOKEN no encontrado en variables de entorno")

# Configurar logging
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=os.getenv("LOG_LEVEL", "INFO"),
    retention="7 days"
)

# Crear consola Rich para mejor output
console = Console()

class MultiAgentSystem:
    """Sistema Multi-Agentes para desarrollo de software usando Agno"""
    
    def __init__(self):
        """Inicializa el sistema multi-agentes"""
        self.project_dir = Path.cwd()
        
        # Crear directorios necesarios
        for dir_name in ["logs", "output", "projects"]:
            (self.project_dir / dir_name).mkdir(exist_ok=True)
        
        # Inicializar workflow con manejo de errores
        try:
            self.workflow = ProjectWorkflow()
            logger.info("Sistema Multi-Agentes inicializado con Agno")
        except Exception as e:
            logger.error(f"Error al inicializar workflow: {e}")
            raise SystemExit("Error al inicializar el sistema. Por favor, verifica la configuración.")

    def _display_plan(self, plan: dict):
        """Muestra el plan en un formato legible"""
        # Título y descripción
        console.print(f"\n[bold blue]# {plan['title']}[/bold blue]")
        console.print(f"\n{plan['description']}\n")
        
        # Tecnologías
        tech_table = Table(title="Tecnologías", show_header=False)
        tech_table.add_column("Tech", style="green")
        for tech in plan['technologies']:
            tech_table.add_row(tech)
        console.print(tech_table)
        
        # Requisitos
        req_table = Table(title="Requisitos", show_header=False)
        req_table.add_column("Req", style="yellow")
        for req in plan['requirements']:
            req_table.add_row(req)
        console.print(req_table)
        
        # Tareas
        task_table = Table(title="Tareas del Proyecto")
        task_table.add_column("ID", style="cyan")
        task_table.add_column("Título", style="blue")
        task_table.add_column("Horas", justify="right", style="green")
        task_table.add_column("Dependencias", style="yellow")
        task_table.add_column("Estado", style="magenta")
        
        for task in plan['tasks']:
            task_table.add_row(
                task['id'],
                task['title'],
                str(task['estimated_hours']),
                ", ".join(task['dependencies']) if task['dependencies'] else "-",
                task['status']
            )
        console.print(task_table)
        
        # Tiempo total
        console.print(f"\n[bold green]Tiempo Total Estimado:[/bold green] {plan['total_estimated_hours']} horas")
        console.print(f"[bold blue]Fecha de Inicio:[/bold blue] {plan['start_date']}\n")
        
        # Arquitectura si está disponible
        if plan.get('architecture'):
            console.print("\n[bold blue]Arquitectura del Sistema:[/bold blue]")
            console.print(Markdown(json.dumps(plan['architecture'], indent=2)))
        
        # Consideraciones de seguridad si están disponibles
        if plan.get('security_considerations'):
            console.print("\n[bold red]Consideraciones de Seguridad:[/bold red]")
            for consideration in plan['security_considerations']:
                console.print(f"• {consideration}")

    async def process_request(self, request: str) -> dict:
        """
        Procesa una solicitud de desarrollo de software
        
        Args:
            request: Descripción del proyecto o tarea
            
        Returns:
            dict: Resultado del procesamiento
        """
        try:
            logger.info(f"Procesando solicitud: {request}")
            
            # Crear plan inicial
            console.print("\n[bold blue]Analizando solicitud y creando plan...[/bold blue]")
            
            try:
                plan_result = await self.workflow.create_project_plan(request)
                logger.info("Plan creado exitosamente")
                logger.debug(f"Plan result: {json.dumps(plan_result, indent=2)}")
            except Exception as e:
                logger.error(f"Error al crear plan: {str(e)}")
                raise Exception(f"Error al crear plan: {str(e)}")
            
            if plan_result.get("status") != "success":
                error_msg = plan_result.get("error", "Error desconocido")
                logger.error(f"Error en el resultado del plan: {error_msg}")
                raise Exception(f"Error al crear plan: {error_msg}")
            
            if not isinstance(plan_result.get("plan"), dict):
                logger.error("El plan no es un diccionario válido")
                raise Exception("El plan generado no tiene el formato correcto")
            
            # Mostrar plan al usuario
            console.print("\n[bold green]Plan del Proyecto:[/bold green]")
            self._display_plan(plan_result["plan"])
            
            # Mostrar análisis y recomendaciones
            console.print("\n[bold blue]Análisis Técnico:[/bold blue]")
            console.print(Markdown(plan_result.get("research", "No hay análisis disponible")))
            
            console.print("\n[bold blue]Diseño Arquitectónico:[/bold blue]")
            console.print(Markdown(plan_result.get("architecture", "No hay diseño disponible")))
            
            console.print("\n[bold red]Análisis de Seguridad:[/bold red]")
            console.print(Markdown(str(plan_result.get("security", "No hay análisis de seguridad disponible"))))
            
            # Preguntar si desea proceder con la implementación
            if Confirm.ask("\n¿Deseas proceder con la implementación del proyecto?"):
                # Crear objeto ProjectPlan desde el diccionario
                plan_dict = plan_result["plan"]
                
                # Asegurarse de que las fechas estén en el formato correcto
                if isinstance(plan_dict.get("start_date"), str):
                    plan_dict["start_date"] = datetime.fromisoformat(plan_dict["start_date"].replace("Z", "+00:00"))
                if isinstance(plan_dict.get("created_at"), str):
                    plan_dict["created_at"] = datetime.fromisoformat(plan_dict["created_at"].replace("Z", "+00:00"))
                if isinstance(plan_dict.get("updated_at"), str):
                    plan_dict["updated_at"] = datetime.fromisoformat(plan_dict["updated_at"].replace("Z", "+00:00"))
                
                # Crear objetos de tareas
                tasks = []
                for task_dict in plan_dict.get("tasks", []):
                    task = ProjectTask(**task_dict)
                    tasks.append(task)
                
                # Reemplazar la lista de tareas en el diccionario
                plan_dict["tasks"] = tasks
                
                # Crear el plan completo
                plan = ProjectPlan(**plan_dict)
                
                # Implementar cada tarea
                console.print("\n[bold blue]Implementando tareas del proyecto...[/bold blue]")
                
                for task in plan.tasks:
                    console.print(f"\n[bold cyan]Implementando tarea: {task.title}[/bold cyan]")
                    
                    implementation_result = await self.workflow.implement_task(task)
                    
                    if implementation_result["status"] != "success":
                        console.print(f"[bold red]Error al implementar tarea: {implementation_result.get('error', 'Error desconocido')}[/bold red]")
                        continue
                    
                    # Mostrar resultados de la implementación
                    console.print("\n[bold green]Código Implementado:[/bold green]")
                    console.print(Markdown(f"```python\n{implementation_result['implementation']}\n```"))
                    
                    console.print("\n[bold yellow]Revisión de Calidad:[/bold yellow]")
                    console.print(Markdown(implementation_result["qa_review"]))
                    
                    console.print("\n[bold red]Revisión de Seguridad:[/bold red]")
                    console.print(Markdown(implementation_result["security_review"]))
                    
                    # Actualizar tarea en el plan
                    task_dict = implementation_result["task"]
                    for i, t in enumerate(plan.tasks):
                        if t.id == task.id:
                            plan.tasks[i] = ProjectTask(**task_dict)
                            break
                    
                    # Ejecutar acciones para esta tarea
                    console.print("\n[bold blue]Ejecutando acciones para esta tarea...[/bold blue]")
                    if hasattr(task, 'files_created') and task.files_created:
                        await self.workflow.process_agent_actions(task.files_created, os.getcwd())
                    if hasattr(task, 'commands_executed') and task.commands_executed:
                        await self.workflow.process_agent_actions(task.commands_executed, os.getcwd())
                
                # Preguntar si desea desplegar el proyecto
                if Confirm.ask("\n¿Deseas desplegar el proyecto?"):
                    console.print("\n[bold blue]Preparando despliegue...[/bold blue]")
                    
                    deployment_result = await self.workflow.deploy_project(plan)
                    
                    if deployment_result["status"] != "success":
                        console.print(f"[bold red]Error al preparar despliegue: {deployment_result['error']}[/bold red]")
                    else:
                        console.print("\n[bold green]Plan de Despliegue:[/bold green]")
                        console.print(Markdown(deployment_result["deployment_plan"]))
                        
                        console.print("\n[bold yellow]Verificación de Calidad:[/bold yellow]")
                        console.print(Markdown(deployment_result["qa_verification"]))
                        
                        console.print("\n[bold red]Verificación de Seguridad:[/bold red]")
                        console.print(Markdown(deployment_result["security_verification"]))
            
            return plan_result
            
        except Exception as e:
            logger.error(f"Error al procesar solicitud: {e}")
            return {"status": "error", "error": str(e)}

async def main():
    """Función principal del sistema"""
    try:
        # Inicializar sistema
        system = MultiAgentSystem()
        logger.info("Sistema iniciado")
        
        # Mostrar mensaje de bienvenida
        welcome_message = """
        Sistema Multi-Agentes para Desarrollo de Software
        
        ¡Bienvenido! Soy tu asistente de IA para desarrollo de software.
        
        Nuestro equipo de agentes especializados incluye:
        • Investigador y Analista Técnico
        • Arquitecto de Software
        • Desarrollador Senior
        • Experto en Control de Calidad
        • Ingeniero DevOps
        • Experto en Seguridad
        
        Juntos podemos planificar, desarrollar y desplegar cualquier tipo de proyecto.
        Por favor, describe tu proyecto o idea en detalle.
        """
        console.print(Panel(welcome_message, title="👋 ¡Hola!", border_style="blue"))
        
        while True:
            # Obtener solicitud del usuario
            request = console.input("\n[bold]Tu proyecto[/bold]: ")
            
            if request.lower() in ["salir", "exit", "quit"]:
                console.print("\n[bold green]¡Gracias por usar el sistema! ¡Hasta pronto![/bold green]")
                break
            
            # Procesar solicitud
            result = await system.process_request(request)
            
            if result["status"] == "error":
                console.print(f"\n[bold red]Error en el sistema: {result['error']}[/bold red]")
                continue
            
            # Preguntar si desea continuar
            if not Confirm.ask("\n¿Deseas realizar otro proyecto?"):
                console.print("\n[bold green]¡Gracias por usar el sistema! ¡Hasta pronto![/bold green]")
                break
                
    except Exception as e:
        logger.error(f"Error en el sistema: {e}")
        console.print(f"\n[bold red]Error crítico en el sistema: {e}[/bold red]")
        raise

if __name__ == "__main__":
    asyncio.run(main())