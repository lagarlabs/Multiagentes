"""
Configuración global del proyecto.
"""
import os
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Union
from dotenv import load_dotenv
from utils.gemini_client import GeminiClient
from utils.openai_client import OpenAIClient
from utils.ai_client_base import AIClientBase

# Cargar variables de entorno
load_dotenv()

class AIManager:
    """Gestor de clientes de IA."""
    
    def __init__(self):
        """Inicializa el gestor de IA."""
        self.primary_client = GeminiClient(os.getenv("GEMINI_API_KEY"), model="gemini-2.5-pro-exp-03-25")
        self.secondary_client = OpenAIClient(os.getenv("OPENAI_API_KEY"))
        self.active_client = self.primary_client
        self.backup_dir = Path("backups")
        self.max_retries = 3  # Número máximo de reintentos antes de cambiar de API
        self.retry_count = 0
        
    def _check_api_availability(self, client: AIClientBase) -> bool:
        """
        Verifica la disponibilidad de la API.
        
        Args:
            client: Cliente de IA a verificar
            
        Returns:
            bool: True si la API está disponible, False en caso contrario
        """
        try:
            # Intenta una operación simple para verificar la API
            client.verify_connection()
            return True
        except Exception as e:
            print(f"Error al verificar la API: {e}")
            return False
            
    def _switch_to_secondary(self):
        """Cambia al cliente secundario."""
        if self.active_client == self.primary_client:
            print("Cambiando a OpenAI como cliente secundario...")
            self.active_client = self.secondary_client
            self.retry_count = 0  # Reiniciar contador de reintentos
        else:
            raise Exception("Ya se está usando el cliente secundario")
        
    def _create_backup(self, project_dir: Path):
        """
        Crea un backup del proyecto.
        
        Args:
            project_dir: Directorio del proyecto
        """
        # Crear directorio de backups si no existe
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear nombre único para el backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{project_dir.name}_backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        # Copiar proyecto
        shutil.copytree(project_dir, backup_path)
        print(f"Backup creado en: {backup_path}")
        
    def execute_with_fallback(self, method_name: str, *args, **kwargs) -> Dict:
        """
        Ejecuta un método con fallback al cliente secundario y sistema de reintentos.
        
        Args:
            method_name: Nombre del método a ejecutar
            *args: Argumentos posicionales
            **kwargs: Argumentos nombrados
            
        Returns:
            Resultado del método
        """
        while self.retry_count < self.max_retries:
            try:
                # Verificar disponibilidad de la API actual
                if not self._check_api_availability(self.active_client):
                    raise Exception("API no disponible")
                
                # Intentar ejecutar el método
                method = getattr(self.active_client, method_name)
                result = method(*args, **kwargs)
                self.retry_count = 0  # Reiniciar contador si la operación fue exitosa
                return result
                
            except Exception as e:
                print(f"Error al ejecutar {method_name}: {e}")
                self.retry_count += 1
                
                if self.retry_count >= self.max_retries:
                    if self.active_client == self.primary_client:
                        self._switch_to_secondary()
                        self.retry_count = 0  # Reiniciar contador para el cliente secundario
                        continue
                    else:
                        # Si ya estamos en el cliente secundario y fallamos, retornar error
                        return {"error": str(e)}
                        
                print(f"Reintentando operación ({self.retry_count}/{self.max_retries})...")
                
        return {"error": "Se alcanzó el número máximo de reintentos"}
        
    def analyze_project(self, project_description: str) -> Dict:
        """
        Analiza un proyecto y genera una estructura de tareas.
        
        Args:
            project_description: Descripción del proyecto
            
        Returns:
            Dict: Estructura de tareas generada
        """
        return self.execute_with_fallback("analyze_project", project_description)
        
    def finalize_project(self, project_dir: Path):
        """
        Finaliza un proyecto creando backup y revisando el código.
        
        Args:
            project_dir: Directorio del proyecto
        """
        # Crear backup
        self._create_backup(project_dir)
        
        # Intentar revisar con el cliente primario
        if self.active_client == self.secondary_client:
            try:
                # Recolectar todos los archivos Python
                python_files = []
                for file in project_dir.rglob("*.py"):
                    with open(file) as f:
                        python_files.append({
                            "path": str(file.relative_to(project_dir)),
                            "code": f.read()
                        })
                
                # Revisar con el cliente primario
                for file in python_files:
                    try:
                        result = self.primary_client.review_code(
                            file["code"],
                            "Revisa el código en busca de errores y mejoras"
                        )
                        print(f"Revisión de {file['path']}: {result}")
                    except Exception as e:
                        print(f"No se pudo revisar {file['path']}: {e}")
            except Exception as e:
                print(f"No se pudo realizar la revisión final: {e}")
                
# Crear instancia global del gestor de IA
ai_manager = AIManager()

"""
Configuración del sistema multi-agentes.
"""

# API Keys
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Configuración de logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = os.getenv('LOG_FORMAT', '<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>')

# Configuración del sistema
MAX_RETRIES = int(os.getenv('MAX_RETRIES', '3'))
TIMEOUT_SECONDS = int(os.getenv('TIMEOUT_SECONDS', '300'))

# Configuración de agentes
DEFAULT_MODEL = os.getenv('DEFAULT_MODEL', 'gemini-2.5-pro-exp-03-25')
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '2000'))

# Validación de configuración
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY no está configurada en el archivo .env")