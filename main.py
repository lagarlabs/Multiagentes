"""
Sistema Multi-Agentes para Desarrollo de Software.
Este módulo implementa una empresa virtual con agentes especializados que colaboran
para completar proyectos de software de forma autónoma.
"""

import os
import asyncio
from pathlib import Path
from loguru import logger
import json
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Confirm
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn

from agents.coordinator_agent import CoordinatorAgent
from agents.market_analysis_agent import MarketAnalysisAgent
from agents.frontend_programmer_agent import FrontendProgrammerAgent
from agents.backend_programmer_agent import BackendProgrammerAgent
from agents.qa_agent import QAAgent
from utils.config_manager import ConfigManager

# Configurar gestor de configuración
config = ConfigManager()

# Configurar logging
logger.add(
    config.get("log_file"),
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level=config.get("log_level"),
    retention="7 days"
)

# Crear consola Rich para mejor output
console = Console()

class MultiAgentCompany:
    """Sistema Multi-Agentes que funciona como una empresa de desarrollo de software"""
    
    def __init__(self):
        """Inicializa la empresa de agentes"""
        self.project_dir = Path.cwd()
        
        # Crear directorios necesarios
        for dir_name in ["logs", "output", "projects", "docs"]:
            (self.project_dir / dir_name).mkdir(exist_ok=True)
        
        # Inicializar agentes con manejo de errores
        try:
            self.coordinator = CoordinatorAgent(self.project_dir)
            self.market_analyst = MarketAnalysisAgent(self.project_dir)
            self.backend_developer = BackendProgrammerAgent(self.project_dir)
            self.frontend_developer = FrontendProgrammerAgent(self.project_dir)
            self.tester = QAAgent(self.project_dir)
            logger.info("Sistema Multi-Agentes inicializado")
        except Exception as e:
            logger.error(f"Error al inicializar agentes: {e}")
            raise SystemExit("Error al inicializar el sistema. Por favor, verifica la configuración.")

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
            
            # Mostrar mensaje de procesamiento
            console.print("\n[bold blue]Iniciando desarrollo del proyecto...[/bold blue]")
            
            # Usar un indicador de progreso para mostrar el avance
            with Progress(
                TextColumn("[bold blue]{task.description}"),
                BarColumn(),
                TimeElapsedColumn()
            ) as progress:
                task = progress.add_task("[bold green]Desarrollando proyecto...", total=100)
                
                # El coordinador maneja todo el proceso de desarrollo
                result = await self.coordinator.process_request(request)
                
                # Simulación de progreso
                while not progress.finished:
                    if result["status"] == "error":
                        progress.update(task, completed=100, description="[bold red]Error en el desarrollo")
                        break
                    progress.update(task, advance=25)
                    await asyncio.sleep(0.1)
                    
            if result["status"] != "success":
                console.print(f"\n[bold red]Error al procesar solicitud: {result.get('error', 'Error desconocido')}[/bold red]")
                
                if "partial_results" in result and result["partial_results"]:
                    console.print("\n[bold yellow]Resultados parciales:[/bold yellow]")
                    console.print(Markdown(json.dumps(result["partial_results"], indent=2)))
                
                return result
            
            # Mostrar resultado
            console.print("\n[bold green]¡Proyecto completado con éxito![/bold green]")
            
            # Mostrar informe final
            self._display_project_report(result["project"])
            
            # Guardar resultados
            output_dir = self.project_dir / "projects" / datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_dir / "project.json", "w", encoding="utf-8") as f:
                json.dump(result["project"], f, indent=2, ensure_ascii=False)
            
            console.print(f"\n[bold green]Resultados guardados en: {output_dir}[/bold green]")
            
            return result
            
        except Exception as e:
            logger.error(f"Error al procesar solicitud: {e}")
            console.print(f"\n[bold red]Error al procesar solicitud: {e}[/bold red]")
            return {"status": "error", "error": str(e)}

    def _display_project_report(self, project: dict):
        """Muestra un informe detallado del proyecto"""
        
        # Título y descripción
        console.print(f"\n[bold blue]# {project.get('project', {}).get('name', 'Proyecto')}[/bold blue]")
        console.print(f"\n{project.get('project', {}).get('description', 'Sin descripción')}\n")
        
        # Mostrar componentes de arquitectura
        if "architecture" in project.get("project", {}):
            console.print("\n[bold blue]Arquitectura:[/bold blue]")
            architecture = project["project"]["architecture"]
            
            if isinstance(architecture, dict):
                # Componentes
                if "components" in architecture and architecture["components"]:
                    comp_table = Table(title="Componentes", show_header=True)
                    comp_table.add_column("Componente", style="green")
                    comp_table.add_column("Descripción", style="blue")
                    
                    for component in architecture["components"]:
                        if isinstance(component, dict) and "name" in component and "description" in component:
                            comp_table.add_row(component["name"], component["description"])
                        elif isinstance(component, str):
                            comp_table.add_row(component, "")
                    
                    console.print(comp_table)
                
                # Interacciones
                if "interactions" in architecture and architecture["interactions"]:
                    console.print("\n[bold yellow]Interacciones entre componentes:[/bold yellow]")
                    for interaction in architecture["interactions"]:
                        console.print(f"• {interaction}")
        
        # Tareas completadas
        if "tasks" in project.get("project", {}):
            task_table = Table(title="Tareas del Proyecto")
            task_table.add_column("ID", style="cyan")
            task_table.add_column("Descripción", style="blue")
            task_table.add_column("Asignado a", style="green")
            task_table.add_column("Estado", style="magenta")
            
            for task in project["project"]["tasks"]:
                task_table.add_row(
                    task.get("id", ""),
                    task.get("description", ""),
                    task.get("assigned_to", ""),
                    task.get("status", "")
                )
            
            console.print(task_table)
        
        # Análisis de mercado
        if "market_verification" in project:
            console.print("\n[bold green]Análisis de Mercado:[/bold green]")
            
            market = project["market_verification"]
            
            if "competitive_advantage" in market:
                console.print(f"\n[bold]Ventaja competitiva:[/bold] {market['competitive_advantage'].get('score', 'N/A')}/10")
                console.print("\n[bold]Fortalezas:[/bold]")
                for strength in market["competitive_advantage"].get("strengths", []):
                    console.print(f"• {strength}")
            
            if "recommendations" in market:
                console.print("\n[bold]Recomendaciones clave:[/bold]")
                for rec in market.get("recommendations", []):
                    if isinstance(rec, dict):
                        console.print(f"• [{rec.get('priority', 'media')}] {rec.get('description', '')}")
                    elif isinstance(rec, str):
                        console.print(f"• {rec}")
        
        # Informe final
        if "final_report" in project:
            console.print("\n[bold blue]Informe Final:[/bold blue]")
            
            if isinstance(project["final_report"], dict) and "summary" in project["final_report"]:
                console.print(Markdown(project["final_report"]["summary"]))
            else:
                console.print(Markdown(json.dumps(project["final_report"], indent=2)))

async def main():
    """Función principal del sistema"""
    try:
        # Inicializar sistema
        system = MultiAgentCompany()
        logger.info("Sistema de empresa multi-agentes iniciado")
        
        # Mostrar mensaje de bienvenida
        welcome_message = """
        # Empresa Virtual de Desarrollo de Software

        ¡Bienvenido! Somos una empresa compuesta por agentes de IA especializados 
        trabajando en conjunto para desarrollar tu proyecto de software.
        
        Nuestro equipo incluye:
        • Coordinador de Proyecto
        • Analista de Mercado
        • Investigador Técnico
        • Desarrollador Backend
        • Desarrollador Frontend
        • Tester y Analista de Calidad
        
        Trabajamos de forma coordinada hasta completar tu proyecto.
        Por favor, describe tu proyecto en detalle y nuestro equipo comenzará a trabajar inmediatamente.
        """
        console.print(Panel(Markdown(welcome_message), title="🏢 Empresa Virtual", border_style="blue"))
        
        while True:
            # Obtener solicitud del usuario
            request = console.input("\n[bold]Describe tu proyecto[/bold]: ")
            
            if request.lower() in ["salir", "exit", "quit"]:
                console.print("\n[bold green]¡Gracias por usar nuestros servicios! ¡Hasta pronto![/bold green]")
                break
            
            # Procesar solicitud (la empresa trabaja de forma autónoma)
            result = await system.process_request(request)
            
            # Preguntar si desea continuar
            if not Confirm.ask("\n¿Deseas iniciar otro proyecto?"):
                console.print("\n[bold green]¡Gracias por usar nuestros servicios! ¡Hasta pronto![/bold green]")
                break
                
    except Exception as e:
        logger.error(f"Error en el sistema: {e}")
        console.print(f"\n[bold red]Error crítico en el sistema: {e}[/bold red]")
        raise

if __name__ == "__main__":
    asyncio.run(main())