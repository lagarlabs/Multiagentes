"""
Sistema de memoria en cascada para los agentes.
Permite almacenar y recuperar información de diferentes fuentes.
"""
import os
import json
import arxiv
import requests
from typing import Dict, List, Optional, Union
from datetime import datetime
from pathlib import Path

class MemorySystem:
    """Sistema de memoria en cascada para los agentes."""
    
    def __init__(self, agent_id: str):
        """
        Inicializa el sistema de memoria.
        
        Args:
            agent_id: ID del agente
        """
        self.agent_id = agent_id
        self.base_dir = Path("memory") / agent_id
        self.short_term = self.base_dir / "short_term"
        self.long_term = self.base_dir / "long_term"
        self.skills = self.base_dir / "skills"
        
        # Crear directorios base
        self.short_term.mkdir(parents=True, exist_ok=True)
        self.long_term.mkdir(parents=True, exist_ok=True)
        self.skills.mkdir(parents=True, exist_ok=True)
        
        # Cliente de Arxiv
        self.arxiv_client = arxiv.Client()
        
    def store_memory(self, content: Dict, memory_type: str = "short_term") -> str:
        """
        Almacena una nueva memoria.
        
        Args:
            content: Contenido de la memoria
            memory_type: Tipo de memoria (short_term, long_term)
            
        Returns:
            ID de la memoria almacenada
        """
        # Crear directorios base si no existen
        if not self.base_dir.exists():
            self.base_dir.mkdir(parents=True, exist_ok=True)
            self.short_term.mkdir(parents=True, exist_ok=True)
            self.long_term.mkdir(parents=True, exist_ok=True)
            self.skills.mkdir(parents=True, exist_ok=True)
        
        # Crear ID único usando microsegundos
        now = datetime.now()
        timestamp = now.strftime('%Y%m%d%H%M%S%f')
        memory_id = f"{self.agent_id}_{memory_type}_{timestamp}"
        
        # Crear estructura de la memoria
        memory = {
            "content": content,
            "created_at": now.isoformat(),
            "last_accessed": now.isoformat(),
            "access_count": 0
        }
        
        # Determinar directorio
        if memory_type == "long_term":
            directory = self.long_term
        elif memory_type == "skills":
            directory = self.skills
        else:
            directory = self.short_term
            
        # Asegurar que el directorio existe
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            
        # Guardar memoria
        memory_file = directory / f"{memory_id}.json"
        with memory_file.open("w") as f:
            json.dump(memory, f, indent=4)
            
        return memory_id
        
    def retrieve_memory(self, memory_id: str) -> Optional[Dict]:
        """
        Recupera una memoria por su ID.
        
        Args:
            memory_id: ID de la memoria
            
        Returns:
            Contenido de la memoria o None si no existe
        """
        # Determinar tipo de memoria y directorio
        if "_short_term_" in memory_id:
            directory = self.short_term
        elif "_long_term_" in memory_id:
            directory = self.long_term
        elif "_skills_" in memory_id:
            directory = self.skills
        else:
            return None
            
        # Buscar archivo de memoria
        memory_file = directory / f"{memory_id}.json"
        if not memory_file.exists():
            return None
            
        # Leer memoria
        with memory_file.open() as f:
            memory = json.load(f)
            
        # Actualizar metadatos
        memory["access_count"] += 1
        memory["last_accessed"] = datetime.now().isoformat()
        
        # Guardar cambios
        with memory_file.open("w") as f:
            json.dump(memory, f, indent=4)
            
        return memory["content"]
        
    def search_memories(self, query: str) -> List[Dict]:
        """
        Busca memorias que coincidan con la consulta.
        
        Args:
            query: Consulta de búsqueda
            
        Returns:
            Lista de memorias que coinciden
        """
        results = []
        query = query.lower()
        
        # Buscar en todas las memorias
        for directory in [self.short_term, self.long_term, self.skills]:
            if not directory.exists():
                continue
                
            for memory_file in directory.glob("*.json"):
                try:
                    with memory_file.open() as f:
                        memory = json.load(f)
                        
                    # Buscar en todo el contenido
                    content = memory.get("content", {})
                    if any(query in str(value).lower() for value in content.values()):
                        results.append(memory)
                except (json.JSONDecodeError, KeyError):
                    continue
                    
        return results
        
    def search_arxiv(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Busca papers relacionados en Arxiv.
        
        Args:
            query: Consulta de búsqueda
            max_results: Número máximo de resultados
            
        Returns:
            Lista de papers encontrados
        """
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for paper in search.results():
            results.append({
                "title": paper.title,
                "summary": paper.summary,
                "authors": [author.name for author in paper.authors],
                "published": paper.published.isoformat(),
                "url": paper.pdf_url,
                "categories": paper.categories
            })
            
            if len(results) >= max_results:
                break
                
        return results
        
    def search_github(self, query: str, language: Optional[str] = None) -> List[Dict]:
        """
        Busca repositorios relacionados en GitHub.
        
        Args:
            query: Consulta de búsqueda
            language: Lenguaje de programación (opcional)
            
        Returns:
            Lista de repositorios encontrados
        """
        # Construir la consulta
        q = query
        if language:
            q += f" language:{language}"
            
        # Realizar la búsqueda
        response = requests.get(
            "https://api.github.com/search/repositories",
            params={"q": q, "sort": "stars", "order": "desc"},
            headers={"Accept": "application/vnd.github.v3+json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            return [{
                "name": repo["name"],
                "description": repo["description"],
                "url": repo["html_url"],
                "stars": repo["stargazers_count"],
                "language": repo["language"],
                "topics": repo.get("topics", [])
            } for repo in data["items"][:5]]
            
        return []
        
    def consolidate_memories(self, min_access_count: int = 5) -> None:
        """
        Consolida las memorias a corto plazo en memorias a largo plazo.
        
        Args:
            min_access_count: Número mínimo de accesos para consolidar
        """
        # Buscar memorias a consolidar
        for memory_file in self.short_term.glob("*.json"):
            with memory_file.open() as f:
                memory = json.load(f)
                
            if memory["access_count"] >= min_access_count:
                # Crear memoria a largo plazo
                long_term_id = f"{self.agent_id}_long_term_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                long_term_file = self.long_term / f"{long_term_id}.json"
                
                with long_term_file.open("w") as f:
                    json.dump(memory, f, indent=4)
                    
                # Eliminar memoria a corto plazo
                memory_file.unlink()
                
    def learn_skill(self, skill_name: str, content: Dict) -> str:
        """
        Almacena una nueva habilidad aprendida.
        
        Args:
            skill_name: Nombre de la habilidad
            content: Contenido de la habilidad
            
        Returns:
            ID de la memoria de habilidad
        """
        return self.store_memory({
            "skill_name": skill_name,
            "content": content
        }, memory_type="skills")
