"""
Sistema de autoaprendizaje para los agentes.
Permite que los agentes mejoren sus habilidades buscando información.
"""
from typing import Dict, List, Optional, Union
from .memory_system import MemorySystem
import asyncio
import re
from datetime import datetime

class SelfLearningSystem:
    """Sistema de autoaprendizaje para los agentes."""
    
    def __init__(self, agent_id: str, memory_system: MemorySystem):
        """
        Inicializa el sistema de autoaprendizaje.
        
        Args:
            agent_id: Identificador del agente
            memory_system: Sistema de memoria del agente
        """
        self.agent_id = agent_id
        self.memory = memory_system
        
    async def learn_about_framework(self, framework: str, language: str) -> Dict:
        """
        Aprende sobre un framework específico buscando información en Arxiv y GitHub.
        
        Args:
            framework: Nombre del framework
            language: Lenguaje de programación
            
        Returns:
            Información recopilada sobre el framework
        """
        query = f"{framework} {language} framework implementation best practices"
        
        # Buscar papers en Arxiv
        arxiv_results = self.memory.search_arxiv(
            query=query,
            max_results=3
        )
        
        # Buscar repositorios en GitHub
        github_results = self.memory.search_github(
            query=query,
            language=language
        )
        
        # Almacenar la información en memoria
        framework_info = {
            "name": framework,
            "language": language,
            "papers": arxiv_results,
            "repositories": github_results,
            "best_practices": [
                "Seguir la documentación oficial",
                "Usar las últimas versiones estables",
                "Implementar pruebas unitarias",
                "Seguir las convenciones de código del lenguaje"
            ]
        }
        
        self.memory.store_memory(framework_info)
        
        return framework_info
        
    def _extract_best_practices(self, papers: List[Dict], repos: List[Dict]) -> List[str]:
        """
        Extrae mejores prácticas de papers y repos.
        
        Args:
            papers: Lista de papers
            repos: Lista de repositorios
            
        Returns:
            Lista de mejores prácticas
        """
        best_practices = set()
        
        # Patrones para identificar mejores prácticas
        patterns = [
            r"best practice[s]?.*?[:\.](.*?)(?=\n|$)",
            r"recommend(?:ed|ation)[s]?.*?[:\.](.*?)(?=\n|$)",
            r"(?:should|must).*?(?:use|implement|follow)(.*?)(?=\n|$)"
        ]
        
        # Extraer de papers
        for paper in papers:
            text = paper["summary"].lower()
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    practice = match.group(1).strip()
                    if len(practice) > 10:  # Filtrar prácticas muy cortas
                        best_practices.add(practice)
                        
        # Extraer de repos
        for repo in repos:
            if repo["description"]:
                text = repo["description"].lower()
                for pattern in patterns:
                    matches = re.finditer(pattern, text, re.IGNORECASE)
                    for match in matches:
                        practice = match.group(1).strip()
                        if len(practice) > 10:
                            best_practices.add(practice)
                            
        return list(best_practices)
        
    async def improve_skills(self, skills: List[str]) -> Dict[str, Dict]:
        """
        Mejora las habilidades del agente.
        
        Args:
            skills: Lista de habilidades a mejorar
            
        Returns:
            Diccionario con la información aprendida para cada habilidad
        """
        results = {}
        
        for skill in skills:
            # Separar lenguaje y framework/herramienta
            if "/" in skill:
                language, framework = skill.split("/")
            else:
                language = skill
                framework = None
                
            # Buscar información específica del lenguaje
            language_info = await self.learn_about_framework(language, language)
            results[language] = language_info
            
            # Si hay un framework específico, buscar información sobre él
            if framework:
                framework_info = await self.learn_about_framework(framework, language)
                results[f"{language}/{framework}"] = framework_info
                
        return results
        
    def analyze_task(self, task: Dict) -> List[str]:
        """
        Analiza una tarea para identificar áreas de mejora.
        
        Args:
            task: Descripción de la tarea
            
        Returns:
            Lista de habilidades que podrían mejorarse
        """
        skills_to_improve = set()
        
        # Extraer habilidades requeridas
        required_skills = task.get("habilidades_requeridas", [])
        for skill in required_skills:
            # Buscar memorias existentes
            existing_memories = self.memory.search_memories(skill)
            
            # Si no hay suficientes memorias, agregar a la lista
            if len(existing_memories) < 2:
                skills_to_improve.add(skill)
                
            # Si las memorias son antiguas, agregar a la lista
            for memory in existing_memories:
                created_at = datetime.fromisoformat(memory["created_at"])
                if (datetime.now() - created_at).days > 30:
                    skills_to_improve.add(skill)
                    break
                    
        return list(skills_to_improve)
        
    async def prepare_for_task(self, task: Dict) -> Dict:
        """
        Prepara al agente para una tarea específica.
        
        Args:
            task: Descripción de la tarea
            
        Returns:
            Información relevante para la tarea
        """
        # Identificar habilidades a mejorar
        skills_to_improve = self.analyze_task(task)
        
        # Mejorar habilidades necesarias
        if skills_to_improve:
            learned_info = await self.improve_skills(skills_to_improve)
        else:
            learned_info = {}
            
        # Buscar memorias relevantes
        relevant_memories = []
        for skill in task.get("habilidades_requeridas", []):
            memories = self.memory.search_memories(skill)
            relevant_memories.extend(memories)
            
        return {
            "improved_skills": learned_info,
            "relevant_memories": relevant_memories,
            "ready_for_task": len(skills_to_improve) == 0 or bool(learned_info)
        }
