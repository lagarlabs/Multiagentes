"""
Gestión centralizada de configuración para el sistema multi-agentes.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv
import logging

class ConfigManager:
    """Gestiona la configuración del sistema"""
    
    _instance = None
    
    def __new__(cls):
        """Implementa patrón Singleton"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa el gestor de configuración"""
        if self._initialized:
            return
            
        # Cargar variables de entorno
        load_dotenv()
        
        # Inicializar configuración por defecto
        self.config = {
            # Modelos
            "default_model": os.getenv("DEFAULT_MODEL", "gpt-4o"),
            "reasoning_model": os.getenv("REASONING_MODEL", "deepseek-reasoner"),
            "temperature": float(os.getenv("TEMPERATURE", "0.7")),
            "max_tokens": int(os.getenv("MAX_TOKENS", "2000")),
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            
            # API Keys
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "exa_api_key": os.getenv("EXA_API_KEY"),
            "github_token": os.getenv("GITHUB_TOKEN"),
            
            # Base de datos
            "database_url": os.getenv("DATABASE_URL", "postgresql://localhost:5432/agno"),
            
            # Logging
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
            "log_file": os.getenv("LOG_FILE", "logs/app.log"),
            
            # Directorios
            "project_dir": Path.cwd(),
            "output_dir": Path.cwd() / "output",
            "logs_dir": Path.cwd() / "logs",
            "projects_dir": Path.cwd() / "projects",
        }
        
        # Verificar configuración crítica
        self._validate_critical_config()
        
        # Crear directorios necesarios
        self._ensure_directories()
        
        self._initialized = True
        logging.info("Gestor de configuración inicializado")
    
    def _validate_critical_config(self):
        """Valida la configuración crítica"""
        # Verificar API keys
        if not self.config["openai_api_key"]:
            logging.error("OPENAI_API_KEY no encontrada en variables de entorno")
            raise ValueError("OPENAI_API_KEY es requerida")
        
        if not self.config["github_token"]:
            logging.warning("GITHUB_TOKEN no encontrado en variables de entorno. Algunas funcionalidades estarán limitadas.")
    
    def _ensure_directories(self):
        """Asegura que los directorios necesarios existan"""
        for dir_path in [self.config["output_dir"], self.config["logs_dir"], self.config["projects_dir"]]:
            dir_path.mkdir(exist_ok=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración
        
        Args:
            key: Clave de configuración
            default: Valor por defecto si no existe
            
        Returns:
            Valor de configuración
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Establece un valor de configuración
        
        Args:
            key: Clave de configuración
            value: Valor a establecer
        """
        self.config[key] = value
        logging.debug(f"Configuración actualizada: {key}={value}")
    
    def get_all(self) -> Dict[str, Any]:
        """
        Obtiene toda la configuración
        
        Returns:
            Diccionario con toda la configuración
        """
        return self.config.copy()
    
    def __str__(self) -> str:
        """Representación en string del objeto"""
        # Filtrar claves sensibles
        safe_config = {k: ("***" if k in ["openai_api_key", "github_token", "exa_api_key"] else v) 
                      for k, v in self.config.items()}
        return f"ConfigManager: {safe_config}"