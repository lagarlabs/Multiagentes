"""
Fábrica de agentes para el sistema multi-agentes.
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.deepseek import DeepSeekChat
from agno.knowledge import AgentKnowledge
from agno.tools.github import GithubTools
from agno.tools.shell import ShellTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.firecrawl import FirecrawlTools

from utils.config_manager import ConfigManager

class AgentFactory:
    """Fábrica para crear agentes especializados"""
    
    def __init__(self, knowledge_base: Optional[AgentKnowledge] = None):
        """
        Inicializa la fábrica de agentes
        
        Args:
            knowledge_base: Base de conocimiento opcional para los agentes
        """
        self.config = ConfigManager()
        self.knowledge_base = knowledge_base
        
        # Inicializar modelos
        self.openai_model = self._create_openai_model()
        self.deepseek_model = self._create_deepseek_model()
        
        # Inicializar herramientas
        self.tools = self._initialize_tools()
    
    def _create_openai_model(self) -> OpenAIChat:
        """
        Crea una instancia del modelo OpenAI
        
        Returns:
            Instancia de OpenAIChat
        """
        return OpenAIChat(
            id=self.config.get("default_model"),
            temperature=self.config.get("temperature"),
            max_tokens=self.config.get("max_tokens"),
            max_retries=self.config.get("max_retries"),
            api_key=self.config.get("openai_api_key")
        )
    
    def _create_deepseek_model(self) -> DeepSeekChat:
        """
        Crea una instancia del modelo DeepSeek
        
        Returns:
            Instancia de DeepSeekChat
        """
        return DeepSeekChat(
            id=self.config.get("reasoning_model")
        )
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """
        Inicializa las herramientas para los agentes
        
        Returns:
            Diccionario con las herramientas inicializadas
        """
        tools = {}
        
        # GitHub Tools
        github_token = self.config.get("github_token")
        if github_token:
            try:
                tools["github"] = GithubTools(github_token)
            except Exception as e:
                print(f"Error al inicializar GithubTools: {str(e)}")
        
        # Otras herramientas
        tools["shell"] = ShellTools()
        tools["search"] = DuckDuckGoTools()
        tools["web"] = FirecrawlTools()
        
        return tools
    
    def create_research_agent(self) -> Agent:
        """
        Crea un agente de investigación
        
        Returns:
            Agente especializado en investigación
        """
        return Agent(
            name="Research Specialist",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[self.tools["search"], self.tools["web"], self.tools["shell"]],
            description=dedent("""\
                Eres un investigador experto en tecnologías y desarrollo de software.
                Tienes la capacidad de ejecutar comandos en la terminal y crear archivos cuando sea necesario.
                Tu especialidad es analizar requisitos técnicos y proponer soluciones óptimas."""),
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
    
    def create_architect_agent(self) -> Agent:
        """
        Crea un agente arquitecto
        
        Returns:
            Agente especializado en arquitectura
        """
        agent_tools = [self.tools["shell"]]
        if "github" in self.tools:
            agent_tools.append(self.tools["github"])
            
        return Agent(
            name="Solution Architect",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=agent_tools,
            description=dedent("""\
                Eres un arquitecto de software experto con capacidad de ejecutar comandos y crear archivos.
                Tu objetivo es diseñar soluciones técnicas robustas y crear la estructura base del proyecto."""),
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
    
    def create_developer_agent(self) -> Agent:
        """
        Crea un agente desarrollador
        
        Returns:
            Agente especializado en desarrollo
        """
        agent_tools = [self.tools["shell"]]
        if "github" in self.tools:
            agent_tools.append(self.tools["github"])
            
        return Agent(
            name="Lead Developer",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=agent_tools,
            description=dedent("""\
                Eres un desarrollador senior con capacidad de ejecutar comandos y crear/modificar archivos.
                Tu objetivo es implementar código de alta calidad y gestionar el proyecto."""),
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
    
    def create_qa_agent(self) -> Agent:
        """
        Crea un agente de QA
        
        Returns:
            Agente especializado en QA
        """
        return Agent(
            name="Quality Assurance",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=[self.tools["shell"]],
            description=dedent("""\
                Eres un experto en control de calidad y testing.
                Tu objetivo es garantizar la calidad y confiabilidad del software."""),
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
    
    def create_security_agent(self) -> Agent:
        """
        Crea un agente de seguridad
        
        Returns:
            Agente especializado en seguridad
        """
        agent_tools = [self.tools["shell"]]
        if "github" in self.tools:
            agent_tools.append(self.tools["github"])
            
        return Agent(
            name="Security Expert",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=agent_tools,
            description=dedent("""\
                Eres un experto en seguridad de aplicaciones.
                Tu misión es identificar y prevenir vulnerabilidades."""),
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
    
    def create_devops_agent(self) -> Agent:
        """
        Crea un agente DevOps
        
        Returns:
            Agente especializado en DevOps
        """
        agent_tools = [self.tools["shell"]]
        if "github" in self.tools:
            agent_tools.append(self.tools["github"])
            
        return Agent(
            name="DevOps Engineer",
            model=self.openai_model,
            knowledge=self.knowledge_base,
            tools=agent_tools,
            description=dedent("""\
                Eres un ingeniero DevOps experimentado.
                Te especializas en automatización, CI/CD y despliegue."""),
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
    
    def create_reasoning_agent(self) -> Agent:
        """
        Crea un agente de razonamiento
        
        Returns:
            Agente especializado en razonamiento
        """
        return Agent(
            model=self.deepseek_model,
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