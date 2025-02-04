"""
Gestor de tareas para el sistema multiagentes.
Este módulo maneja la creación, asignación y seguimiento de tareas.
"""

from typing import List, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from loguru import logger

class Task(BaseModel):
    """Modelo de tarea para el sistema"""
    id: str
    title: str
    description: str
    status: str
    assigned_to: Optional[str]
    created_at: datetime
    updated_at: datetime
    dependencies: List[str] = []
    priority: int = 1
    progress: float = 0.0
    metadata: Dict = {}

class TaskManager:
    """Gestor principal de tareas"""
    
    def __init__(self):
        """Inicializa el gestor de tareas"""
        self.tasks: Dict[str, Task] = {}
        logger.info("TaskManager inicializado")
    
    def create_task(self, title: str, description: str, **kwargs) -> Task:
        """Crea una nueva tarea"""
        task_id = f"task_{len(self.tasks) + 1}"
        now = datetime.now()
        
        task = Task(
            id=task_id,
            title=title,
            description=description,
            status="pending",
            created_at=now,
            updated_at=now,
            **kwargs
        )
        
        self.tasks[task_id] = task
        logger.info(f"Tarea creada: {task_id} - {title}")
        return task
    
    def assign_task(self, task_id: str, agent_id: str) -> Task:
        """Asigna una tarea a un agente"""
        if task_id not in self.tasks:
            raise ValueError(f"Tarea {task_id} no encontrada")
            
        task = self.tasks[task_id]
        task.assigned_to = agent_id
        task.status = "in_progress"
        task.updated_at = datetime.now()
        
        logger.info(f"Tarea {task_id} asignada a {agent_id}")
        return task
    
    def update_task_status(self, task_id: str, status: str, progress: float = None) -> Task:
        """Actualiza el estado de una tarea"""
        if task_id not in self.tasks:
            raise ValueError(f"Tarea {task_id} no encontrada")
            
        task = self.tasks[task_id]
        task.status = status
        task.updated_at = datetime.now()
        
        if progress is not None:
            task.progress = progress
            
        logger.info(f"Tarea {task_id} actualizada: estado={status}, progreso={progress}")
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Obtiene una tarea por su ID"""
        return self.tasks.get(task_id)
    
    def get_tasks_by_agent(self, agent_id: str) -> List[Task]:
        """Obtiene todas las tareas asignadas a un agente"""
        return [task for task in self.tasks.values() if task.assigned_to == agent_id]
    
    def get_pending_tasks(self) -> List[Task]:
        """Obtiene todas las tareas pendientes"""
        return [task for task in self.tasks.values() if task.status == "pending"]
    
    def get_completed_tasks(self) -> List[Task]:
        """Obtiene todas las tareas completadas"""
        return [task for task in self.tasks.values() if task.status == "completed"]
