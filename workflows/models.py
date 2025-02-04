"""
Modelos de datos para el workflow de proyectos
"""

from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ProjectTask(BaseModel):
    """Representa una tarea del proyecto"""
    id: str
    title: str
    description: str
    estimated_hours: float
    dependencies: List[str] = []
    status: str = "pending"
    files_created: List[str] = []
    commands_executed: List[str] = []
    assigned_to: Optional[str] = None
    code: Optional[str] = None
    tests: Optional[str] = None
    review_comments: Optional[List[str]] = None

class ProjectPlan(BaseModel):
    """Representa un plan de proyecto completo"""
    title: str
    description: str
    tasks: List[ProjectTask]
    total_estimated_hours: float
    technologies: List[str]
    requirements: List[str]
    architecture: Dict
    security_considerations: List[str] = []
    start_date: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    actions_taken: List[str] = []
