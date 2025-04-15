"""
Agente Coordinador del sistema multiagentes.
Este agente se encarga de coordinar las tareas entre los demás agentes.
"""

from typing import Dict, List, Optional, Any
from loguru import logger
import json
from datetime import datetime
import os
from pathlib import Path
from textwrap import dedent
import asyncio

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeekChat

from .programmer_agent import ProgrammerAgent
from .qa_agent import QAAgent
from .market_analysis_agent import MarketAnalysisAgent
from .frontend_programmer_agent import FrontendProgrammerAgent
from .backend_programmer_agent import BackendProgrammerAgent
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
        # Inicializar todos los agentes
        self.researcher = ProgrammerAgent(working_dir)
        self.qa = QAAgent(working_dir)
        self.market_analyst = MarketAnalysisAgent(working_dir)
        self.frontend_developer = FrontendProgrammerAgent(working_dir)
        self.backend_developer = BackendProgrammerAgent(working_dir)
        self.current_project = None
        self.project_status = "not_started"
        logger.info("Agente Coordinador inicializado con todos los especialistas")

    async def process_request(self, request: str) -> Dict:
        """
        Procesa una solicitud de proyecto e inicia el flujo completo de desarrollo
        
        Args:
            request (str): Descripción del proyecto
            
        Returns:
            Dict: Resultado del procesamiento
        """
        try:
            logger.info(f"Iniciando nuevo proyecto: {request}")
            self.project_status = "started"
            
            # Fase 1: Investigación y Análisis
            analysis_result = await self._phase_research_analysis(request)
            if analysis_result["status"] != "success":
                raise Exception(f"Error en fase de investigación: {analysis_result.get('error', 'Error desconocido')}")
            
            # Fase 2: Diseño de arquitectura
            architecture_result = await self._phase_architecture_design(request, analysis_result)
            if architecture_result["status"] != "success":
                raise Exception(f"Error en fase de diseño: {architecture_result.get('error', 'Error desconocido')}")
            
            # Fase 3: Análisis de mercado
            market_result = await self._phase_market_analysis(request, architecture_result)
            if market_result["status"] != "success":
                raise Exception(f"Error en análisis de mercado: {market_result.get('error', 'Error desconocido')}")
            
            # Fase 4: Implementación (Backend y Frontend en paralelo)
            implementation_result = await self._phase_implementation(architecture_result, market_result)
            if implementation_result["status"] != "success":
                raise Exception(f"Error en implementación: {implementation_result.get('error', 'Error desconocido')}")
            
            # Fase 5: Testing y QA
            testing_result = await self._phase_testing(implementation_result)
            if testing_result["status"] != "success":
                raise Exception(f"Error en testing: {testing_result.get('error', 'Error desconocido')}")
            
            # Fase 6: Ajustes finales según feedback de mercado
            final_result = await self._phase_final_adjustments(implementation_result, testing_result, market_result)
            if final_result["status"] != "success":
                raise Exception(f"Error en ajustes finales: {final_result.get('error', 'Error desconocido')}")
            
            # Guardar el resultado final del proyecto
            self.current_project = final_result["project"]
            self.project_status = "completed"
            
            logger.info(f"Proyecto completado con éxito: {self.current_project.get('name', 'Sin nombre')}")
            
            return {
                "status": "success",
                "project": self.current_project,
                "processed_at": datetime.now().isoformat(),
                "phases_completed": [
                    "research_analysis",
                    "architecture_design",
                    "market_analysis",
                    "implementation",
                    "testing",
                    "final_adjustments"
                ]
            }
                
        except Exception as e:
            logger.error(f"Error al procesar solicitud: {str(e)}")
            self.project_status = "error"
            return {
                "status": "error",
                "error": str(e),
                "partial_results": self.current_project
            }

    async def _phase_research_analysis(self, request: str) -> Dict:
        """
        Fase 1: Investigación y análisis inicial
        
        Args:
            request (str): Solicitud del usuario
            
        Returns:
            Dict: Resultado del análisis
        """
        try:
            # Primero usar el agente de razonamiento para analizar y diseñar
            analysis_prompt = f"""
            Analiza la siguiente solicitud de proyecto y diseña una solución:
            
            SOLICITUD:
            {request}
            
            Proporciona:
            1. Análisis detallado de requerimientos
            2. Arquitectura propuesta inicial
            3. Tecnologías recomendadas
            4. Desafíos técnicos a considerar
            """
            
            analysis_response = await self.reasoning_agent.arun(analysis_prompt)
            
            # Pasar la investigación al agente investigador para profundizar
            research_response = await self.researcher.generate_implementation({
                "description": f"Investigar y analizar los siguientes aspectos del proyecto: {request}",
                "constraints": "Debe ser exhaustivo y considerar las últimas tecnologías disponibles",
                "technologies": "Investigar las mejores opciones para este proyecto",
                "initial_analysis": analysis_response.content
            })
            
            if research_response["status"] != "success":
                raise Exception(f"Error en investigación: {research_response.get('error', 'Error desconocido')}")
            
            return {
                "status": "success",
                "analysis": analysis_response.content,
                "research": research_response["implementation"],
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en fase de investigación: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _phase_architecture_design(self, request: str, research_result: Dict) -> Dict:
        """
        Fase 2: Diseño de arquitectura
        
        Args:
            request (str): Solicitud del usuario
            research_result (Dict): Resultado de la investigación
            
        Returns:
            Dict: Resultado del diseño de arquitectura
        """
        try:
            # Crear prompt para diseñar la arquitectura basada en la investigación
            architecture_prompt = f"""
            Diseña una arquitectura detallada para el proyecto basada en la investigación:
            
            SOLICITUD ORIGINAL:
            {request}
            
            INVESTIGACIÓN:
            {research_result["research"]}
            
            ANÁLISIS PREVIO:
            {research_result["analysis"]}
            
            Diseña:
            1. Arquitectura general del sistema
            2. Componentes principales (backend, frontend, servicios)
            3. Patrones de diseño a utilizar
            4. Modelo de datos
            5. Flujo de interacción entre componentes
            """
            
            architecture_response = await self.reasoning_agent.arun(architecture_prompt)
            
            # Crear plan de proyecto basado en la arquitectura diseñada
            planning_prompt = f"""
            Crea un plan de proyecto basado en la siguiente arquitectura:
            
            ARQUITECTURA:
            {architecture_response.content}
            
            SOLICITUD ORIGINAL:
            {request}
            
            INVESTIGACIÓN:
            {research_result["research"]}
            
            Genera un plan detallado siguiendo el formato JSON especificado.
            El plan debe incluir tareas para backend, frontend, integración y pruebas.
            """
            
            response = await self.agent.arun(planning_prompt)
            
            try:
                plan = parse_agent_response(response.content, "respuesta del plan")
                self.current_project = plan
                
                return {
                    "status": "success",
                    "architecture": architecture_response.content,
                    "plan": plan,
                    "completed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Error al procesar respuesta JSON: {str(e)}",
                    "raw_response": response.content
                }
                
        except Exception as e:
            logger.error(f"Error en fase de diseño: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _phase_market_analysis(self, request: str, architecture_result: Dict) -> Dict:
        """
        Fase 3: Análisis de mercado
        
        Args:
            request (str): Solicitud del usuario
            architecture_result (Dict): Resultado del diseño de arquitectura
            
        Returns:
            Dict: Resultado del análisis de mercado
        """
        try:
            # Preparar los detalles del proyecto para el análisis de mercado
            project_details = {
                "description": request,
                "architecture": architecture_result["architecture"],
                "technologies": architecture_result["plan"]["project"].get("technologies", []),
                "features": [task["description"] for task in architecture_result["plan"]["project"].get("tasks", [])]
            }
            
            # Realizar análisis de mercado
            market_analysis = await self.market_analyst.analyze_market_fit(project_details)
            
            if market_analysis["status"] != "success":
                raise Exception(f"Error en análisis de mercado: {market_analysis.get('error', 'Error desconocido')}")
            
            # Obtener recomendaciones basadas en el análisis
            recommendations = await self.market_analyst.recommend_improvements(project_details, market_analysis["analysis"])
            
            if recommendations["status"] != "success":
                raise Exception(f"Error en recomendaciones: {recommendations.get('error', 'Error desconocido')}")
            
            # Actualizar el plan de proyecto con los insights del mercado
            update_prompt = f"""
            Actualiza el plan de proyecto con los insights del análisis de mercado:
            
            PLAN ACTUAL:
            {json.dumps(architecture_result["plan"], indent=2)}
            
            ANÁLISIS DE MERCADO:
            {json.dumps(market_analysis["analysis"], indent=2)}
            
            RECOMENDACIONES:
            {json.dumps(recommendations["recommendations"], indent=2)}
            
            Actualiza el plan manteniendo el formato JSON original.
            Añade o modifica tareas para incorporar las recomendaciones del análisis de mercado.
            """
            
            response = await self.agent.arun(update_prompt)
            
            try:
                updated_plan = parse_agent_response(response.content, "respuesta del plan actualizado")
                self.current_project = updated_plan
                
                return {
                    "status": "success",
                    "market_analysis": market_analysis["analysis"],
                    "recommendations": recommendations["recommendations"],
                    "updated_plan": updated_plan,
                    "completed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta JSON: {str(e)}")
                return {
                    "status": "error",
                    "error": f"Error al procesar respuesta JSON: {str(e)}",
                    "raw_response": response.content
                }
                
        except Exception as e:
            logger.error(f"Error en fase de análisis de mercado: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _phase_implementation(self, architecture_result: Dict, market_result: Dict) -> Dict:
        """
        Fase 4: Implementación (Backend y Frontend en paralelo)
        
        Args:
            architecture_result (Dict): Resultado del diseño de arquitectura
            market_result (Dict): Resultado del análisis de mercado
            
        Returns:
            Dict: Resultado de la implementación
        """
        try:
            # Extraer tareas de backend
            backend_tasks = [task for task in market_result["updated_plan"]["project"]["tasks"] 
                           if "backend" in task["description"].lower() or "api" in task["description"].lower() 
                           or "database" in task["description"].lower() or "servidor" in task["description"].lower()]
            
            # Extraer tareas de frontend
            frontend_tasks = [task for task in market_result["updated_plan"]["project"]["tasks"] 
                            if "frontend" in task["description"].lower() or "interfaz" in task["description"].lower() 
                            or "ui" in task["description"].lower() or "ux" in task["description"].lower() 
                            or "cliente" in task["description"].lower()]
            
            # Ejecutar implementación backend
            backend_implementations = []
            for task in backend_tasks:
                logger.info(f"Implementando tarea backend: {task['id']} - {task['description']}")
                
                # Preparar requerimientos
                requirements = {
                    "description": task["description"],
                    "constraints": task.get("constraints", ""),
                    "technologies": market_result["updated_plan"]["project"].get("technologies", []),
                    "architecture": architecture_result["architecture"]
                }
                
                # Implementar backend
                backend_impl = await self.backend_developer.implement_api(requirements, {})  # DB design vacío por ahora
                
                if backend_impl["status"] != "success":
                    raise Exception(f"Error en implementación backend ({task['id']}): {backend_impl.get('error', 'Error desconocido')}")
                
                backend_implementations.append({
                    "task_id": task["id"],
                    "implementation": backend_impl["api_implementation"],
                    "design": backend_impl["design"]
                })
                
                # Actualizar estado de la tarea
                task["status"] = "completed"
                task["implementation"] = backend_impl["api_implementation"]
            
            # Ejecutar implementación frontend
            frontend_implementations = []
            for task in frontend_tasks:
                logger.info(f"Implementando tarea frontend: {task['id']} - {task['description']}")
                
                # Detectar framework de frontend
                technologies = market_result["updated_plan"]["project"].get("technologies", [])
                frontend_framework = next((tech for tech in technologies if tech.lower() in 
                                        ["react", "vue", "angular", "svelte"]), "react")
                
                # Preparar requerimientos
                requirements = {
                    "description": task["description"],
                    "application_type": "web",
                    "target_users": ["usuarios finales"],
                    "features": [task["description"]],
                    "technologies": technologies
                }
                
                # Diseñar UI
                ui_design = await self.frontend_developer.design_ui(requirements)
                
                if ui_design["status"] != "success":
                    raise Exception(f"Error en diseño UI ({task['id']}): {ui_design.get('error', 'Error desconocido')}")
                
                # Implementar componentes
                components = await self.frontend_developer.implement_components(ui_design["ui_design"], frontend_framework)
                
                if components["status"] != "success":
                    raise Exception(f"Error en implementación frontend ({task['id']}): {components.get('error', 'Error desconocido')}")
                
                frontend_implementations.append({
                    "task_id": task["id"],
                    "ui_design": ui_design["ui_design"],
                    "components": components["components"],
                    "architecture": components["architecture"]
                })
                
                # Actualizar estado de la tarea
                task["status"] = "completed"
                task["implementation"] = {
                    "ui_design": ui_design["ui_design"],
                    "components": components["components"]
                }
            
            # Actualizar plan del proyecto
            updated_plan = market_result["updated_plan"]
            for task in backend_tasks + frontend_tasks:
                for i, t in enumerate(updated_plan["project"]["tasks"]):
                    if t["id"] == task["id"]:
                        updated_plan["project"]["tasks"][i] = task
                        break
            
            self.current_project = updated_plan
            
            return {
                "status": "success",
                "backend_implementations": backend_implementations,
                "frontend_implementations": frontend_implementations,
                "updated_plan": updated_plan,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en fase de implementación: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def _phase_testing(self, implementation_result: Dict) -> Dict:
        """
        Fase 5: Testing y QA
        
        Args:
            implementation_result (Dict): Resultado de la implementación
            
        Returns:
            Dict: Resultado del testing
        """
        try:
            # Recopilar todas las implementaciones
            implementations = []
            
            # Añadir implementaciones de backend
            for impl in implementation_result["backend_implementations"]:
                implementations.append({
                    "task_id": impl["task_id"],
                    "type": "backend",
                    "code": impl["implementation"],
                    "tests": impl["implementation"].get("tests", {})
                })
            
            # Añadir implementaciones de frontend
            for impl in implementation_result["frontend_implementations"]:
                implementations.append({
                    "task_id": impl["task_id"],
                    "type": "frontend",
                    "code": impl["components"],
                    "tests": impl["components"].get("tests", {})
                })
            
            # Realizar testing de cada implementación
            test_results = []
            for impl in implementations:
                logger.info(f"Testeando implementación: {impl['task_id']} ({impl['type']})")
                
                # Realizar revisión de QA
                review = await self.qa.perform_review({
                    "code": impl["code"],
                    "documentation": impl["code"].get("documentation", {}),
                    "tests": impl["tests"]
                })
                
                if review["status"] != "success":
                    raise Exception(f"Error en QA ({impl['task_id']}): {review.get('error', 'Error desconocido')}")
                
                test_results.append({
                    "task_id": impl["task_id"],
                    "type": impl["type"],
                    "review": review["review"],
                    "reasoning": review["reasoning"]
                })
                
                # Si no se aprueba, refactorizar
                if not review["review"].get("approved", False):
                    logger.warning(f"Refactorizando implementación: {impl['task_id']} ({impl['type']})")
                    
                    if impl["type"] == "backend":
                        # Encontrar la implementación original
                        orig_impl = next((bi for bi in implementation_result["backend_implementations"] 
                                        if bi["task_id"] == impl["task_id"]), None)
                        
                        if orig_impl:
                            refactored = await self.backend_developer.implement_business_logic(
                                {"description": "Refactorizar código según feedback de QA", 
                                 "feedback": review["review"]},
                                {"design": orig_impl["design"]}
                            )
                            
                            if refactored["status"] == "success":
                                # Actualizar la implementación
                                impl["code"] = refactored["business_logic"]
                                # Encontrar y actualizar la tarea en el plan
                                self._update_task_implementation(implementation_result["updated_plan"], 
                                                               impl["task_id"], refactored["business_logic"])
                    
                    elif impl["type"] == "frontend":
                        # Encontrar la implementación original
                        orig_impl = next((fi for fi in implementation_result["frontend_implementations"] 
                                        if fi["task_id"] == impl["task_id"]), None)
                        
                        if orig_impl:
                            refactored = await self.frontend_developer.implement_components(
                                orig_impl["ui_design"],
                                "react",  # Default framework
                                review["review"]
                            )
                            
                            if refactored["status"] == "success":
                                # Actualizar la implementación
                                impl["code"] = refactored["components"]
                                # Encontrar y actualizar la tarea en el plan
                                self._update_task_implementation(implementation_result["updated_plan"], 
                                                               impl["task_id"], refactored["components"])
            
            # Actualizar plan con los resultados de testing
            updated_plan = implementation_result["updated_plan"]
            for test_result in test_results:
                for i, task in enumerate(updated_plan["project"]["tasks"]):
                    if task["id"] == test_result["task_id"]:
                        task["qa_review"] = test_result["review"]
                        updated_plan["project"]["tasks"][i] = task
                        break
            
            self.current_project = updated_plan
            
            return {
                "status": "success",
                "test_results": test_results,
                "updated_plan": updated_plan,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en fase de testing: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _update_task_implementation(self, plan: Dict, task_id: str, new_implementation: Any) -> None:
        """
        Actualiza la implementación de una tarea en el plan
        
        Args:
            plan (Dict): Plan de proyecto
            task_id (str): ID de la tarea
            new_implementation (Any): Nueva implementación
        """
        for i, task in enumerate(plan["project"]["tasks"]):
            if task["id"] == task_id:
                task["implementation"] = new_implementation
                plan["project"]["tasks"][i] = task
                break

    async def _phase_final_adjustments(self, implementation_result: Dict, testing_result: Dict, market_result: Dict) -> Dict:
        """
        Fase 6: Ajustes finales según feedback de mercado
        
        Args:
            implementation_result (Dict): Resultado de la implementación
            testing_result (Dict): Resultado del testing
            market_result (Dict): Resultado del análisis de mercado
            
        Returns:
            Dict: Resultado de los ajustes finales
        """
        try:
            # Recopilar todo el trabajo realizado hasta ahora
            plan = testing_result["updated_plan"]
            
            # Verificar si el proyecto cumple con las recomendaciones de mercado
            market_verification_prompt = f"""
            Verifica si el proyecto implementado cumple con las recomendaciones de mercado:
            
            PROYECTO ACTUAL:
            {json.dumps(plan, indent=2)}
            
            RECOMENDACIONES DE MERCADO:
            {json.dumps(market_result["recommendations"], indent=2)}
            
            ANÁLISIS DE MERCADO:
            {json.dumps(market_result["market_analysis"], indent=2)}
            
            Evalúa:
            1. ¿Se han implementado las recomendaciones clave?
            2. ¿El proyecto tiene ventajas competitivas diferenciadas?
            3. ¿Hay oportunidades de mejora pendientes?
            4. ¿El proyecto está listo para el mercado?
            """
            
            market_verification = await self.market_analyst.analyze_market_fit({
                "description": "Verificación final de ajuste al mercado",
                "technologies": plan["project"].get("technologies", []),
                "features": [task["description"] for task in plan["project"]["tasks"]]
            })
            
            if market_verification["status"] != "success":
                raise Exception(f"Error en verificación de mercado: {market_verification.get('error', 'Error desconocido')}")
            
            # Crear informe final del proyecto
            final_report_prompt = f"""
            Genera un informe final del proyecto:
            
            PROYECTO:
            {json.dumps(plan, indent=2)}
            
            VERIFICACIÓN DE MERCADO:
            {json.dumps(market_verification["analysis"], indent=2)}
            
            El informe debe incluir:
            1. Resumen ejecutivo
            2. Logros principales
            3. Arquitectura implementada
            4. Características destacadas
            5. Ventajas competitivas
            6. Próximos pasos recomendados
            """
            
            final_report_response = await self.agent.arun(final_report_prompt)
            
            try:
                final_report = parse_agent_response(final_report_response.content, "informe final")
                
                # Actualizar plan con el informe final
                plan["final_report"] = final_report
                plan["market_verification"] = market_verification["analysis"]
                
                self.current_project = plan
                
                return {
                    "status": "success",
                    "project": plan,
                    "market_verification": market_verification["analysis"],
                    "final_report": final_report,
                    "completed_at": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error al procesar informe final: {str(e)}")
                return {
                    "status": "error", 
                    "error": f"Error al procesar informe final: {str(e)}",
                    "raw_response": final_report_response.content
                }
                
        except Exception as e:
            logger.error(f"Error en fase de ajustes finales: {str(e)}")
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
            "status": self.project_status,
            "current_project": self.current_project,
            "working_dir": str(self.working_dir)
        }