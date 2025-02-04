"""
Pruebas unitarias para el sistema de memoria y autoaprendizaje.
"""
import os
import json
import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from utils.memory_system import MemorySystem
from utils.self_learning import SelfLearningSystem

@pytest.fixture
def memory_system():
    """Fixture que proporciona un sistema de memoria para pruebas."""
    # Crear sistema de memoria
    memory = MemorySystem("test_agent")
    
    # Limpiar directorios existentes
    if memory.base_dir.exists():
        for file in memory.base_dir.glob("**/*"):
            if file.is_file():
                file.unlink()
        for dir in reversed(list(memory.base_dir.glob("**/*"))):
            if dir.is_dir():
                dir.rmdir()
        memory.base_dir.rmdir()
        
    # Crear directorios nuevos
    memory.base_dir.mkdir(parents=True, exist_ok=True)
    memory.short_term.mkdir(parents=True, exist_ok=True)
    memory.long_term.mkdir(parents=True, exist_ok=True)
    memory.skills.mkdir(parents=True, exist_ok=True)
    
    yield memory
    
    # Limpiar después de las pruebas
    if memory.base_dir.exists():
        for file in memory.base_dir.glob("**/*"):
            if file.is_file():
                file.unlink()
        for dir in reversed(list(memory.base_dir.glob("**/*"))):
            if dir.is_dir():
                dir.rmdir()
        memory.base_dir.rmdir()
        
@pytest.fixture
def learning_system(memory_system):
    """Fixture que proporciona un sistema de autoaprendizaje para pruebas."""
    return SelfLearningSystem("test_agent", memory_system)

def test_store_and_retrieve_memory(memory_system):
    """Prueba el almacenamiento y recuperación de memorias."""
    # Almacenar una memoria
    content = {
        "skill": "python",
        "framework": "fastapi",
        "example": "print('Hello World')"
    }
    
    memory_id = memory_system.store_memory(content)
    
    # Recuperar la memoria
    retrieved = memory_system.retrieve_memory(memory_id)
    
    # Verificar que el contenido sea el mismo
    assert retrieved == content
    
def test_search_memories(memory_system):
    """Prueba la búsqueda de memorias."""
    # Almacenar varias memorias
    memories = [
        {
            "skill": "python",
            "framework": "fastapi",
            "example": "print('Hello World')"
        },
        {
            "skill": "javascript",
            "framework": "react",
            "example": "console.log('Hello World')"
        },
        {
            "skill": "python",
            "framework": "django",
            "example": "print('Django App')"
        }
    ]
    
    for memory in memories:
        memory_system.store_memory(memory)
        
    # Buscar memorias de Python
    results = memory_system.search_memories("python")
    assert len([r for r in results if "python" in str(r["content"])]) == 2
    
    # Buscar memorias de React
    results = memory_system.search_memories("react")
    assert len([r for r in results if "react" in str(r["content"])]) == 1
    
def test_consolidate_memories(memory_system):
    """Prueba la consolidación de memorias."""
    # Almacenar memorias a corto plazo
    content = {
        "skill": "python",
        "framework": "fastapi",
        "example": "print('Hello World')"
    }
    
    memory_id = memory_system.store_memory(content, memory_type="short_term")
    
    # Simular accesos múltiples
    for _ in range(5):
        memory_system.retrieve_memory(memory_id)
        
    # Consolidar memorias
    memory_system.consolidate_memories()
    
    # Verificar que la memoria se movió a largo plazo
    assert not (memory_system.short_term / f"{memory_id}.json").exists()
    assert len(list(memory_system.long_term.glob("*.json"))) == 1
    
@pytest.mark.asyncio
async def test_learn_about_framework(learning_system):
    """Prueba el aprendizaje sobre frameworks."""
    # Aprender sobre FastAPI
    framework_info = await learning_system.learn_about_framework("fastapi", "python")
    
    # Verificar la estructura de la información
    assert isinstance(framework_info, dict)
    assert "name" in framework_info
    assert "language" in framework_info
    assert "papers" in framework_info
    assert "repositories" in framework_info
    assert "best_practices" in framework_info
    
@pytest.mark.asyncio
async def test_improve_skills(learning_system):
    """Prueba la mejora de habilidades."""
    # Mejorar habilidades específicas
    skills = ["python/fastapi", "javascript/react"]
    results = await learning_system.improve_skills(skills)
    
    # Verificar que se aprendió sobre cada habilidad
    assert isinstance(results, dict)
    assert "python" in results
    assert "python/fastapi" in results
    assert "javascript" in results
    assert "javascript/react" in results
    
def test_analyze_task(learning_system):
    """Prueba el análisis de tareas."""
    # Crear una tarea de ejemplo
    task = {
        "id": 1,
        "descripcion": "Implementar una API REST con FastAPI",
        "habilidades_requeridas": ["python", "fastapi", "sql"]
    }
    
    # Analizar la tarea
    skills_to_improve = learning_system.analyze_task(task)
    
    # Verificar que se identificaron las habilidades a mejorar
    assert isinstance(skills_to_improve, list)
    assert all(isinstance(skill, str) for skill in skills_to_improve)
    
@pytest.mark.asyncio
async def test_prepare_for_task(learning_system):
    """Prueba la preparación para una tarea."""
    # Crear una tarea de ejemplo
    task = {
        "id": 1,
        "descripcion": "Implementar una API REST con FastAPI",
        "habilidades_requeridas": ["python", "fastapi", "sql"]
    }
    
    # Preparar para la tarea
    preparation = await learning_system.prepare_for_task(task)
    
    # Verificar la estructura del resultado
    assert isinstance(preparation, dict)
    assert "improved_skills" in preparation
    assert "relevant_memories" in preparation
    assert "ready_for_task" in preparation
    assert isinstance(preparation["ready_for_task"], bool)
