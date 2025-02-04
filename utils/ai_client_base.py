"""
Cliente base abstracto para APIs de IA.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class AIClientBase(ABC):
    """Clase base abstracta para clientes de IA."""
    
    def __init__(self, api_key: str):
        """
        Inicializa el cliente base.
        
        Args:
            api_key (str): Clave API del servicio
        """
        self.api_key = api_key
        
    @abstractmethod
    def analyze_project(self, description: str) -> Dict:
        """
        Analiza un proyecto y genera una estructura de tareas.
        
        Args:
            description: Descripción del proyecto
            
        Returns:
            Diccionario con la estructura de tareas
        """
        pass
        
    @abstractmethod
    def generate_code(self, task_description: str) -> Dict:
        """
        Genera código para una tarea.
        
        Args:
            task_description: Descripción de la tarea
            
        Returns:
            Diccionario con el código generado
        """
        pass
        
    @abstractmethod
    def review_code(self, code: str, requirements: str) -> Dict:
        """
        Revisa código generado.
        
        Args:
            code: Código a revisar
            requirements: Requerimientos del código
            
        Returns:
            Diccionario con el resultado de la revisión
        """
        pass
        
    @abstractmethod
    def test_code(self, code: str, test_requirements: str) -> Dict:
        """
        Genera tests para el código.
        
        Args:
            code: Código a testear
            test_requirements: Requerimientos de los tests
            
        Returns:
            Diccionario con los tests generados
        """
        pass
        
    @abstractmethod
    def verify_connection(self) -> bool:
        """
        Verifica la disponibilidad de la API.
        
        Returns:
            bool: True si la API está disponible, False en caso contrario
        """
        pass
