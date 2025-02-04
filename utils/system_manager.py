"""
Gestor avanzado del sistema operativo y recursos del ordenador.
"""
import os
import sys
import psutil
import shutil
import subprocess
import json
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from datetime import datetime

try:
    import docker
    import git
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False

class SystemManager:
    """Gestor avanzado del sistema con capacidades extendidas."""
    
    def __init__(self, working_dir: Optional[Path] = None, max_workers: int = 4):
        """
        Inicializa el gestor del sistema.
        
        Args:
            working_dir: Directorio de trabajo
            max_workers: Número máximo de workers para procesamiento paralelo
        """
        self.working_dir = working_dir or Path.cwd()
        self.thread_pool = ThreadPoolExecutor(max_workers=max_workers)
        self.process_pool = ProcessPoolExecutor(max_workers=max_workers)
        self.docker_client = None
        if DOCKER_AVAILABLE and self._check_docker():
            try:
                self.docker_client = docker.from_env()
            except:
                pass
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Configura el sistema de logging."""
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)
        
        # Crear directorio de logs si no existe
        log_dir = self.working_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Handler para archivo
        file_handler = logging.FileHandler(
            log_dir / f"system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
        
    def _check_docker(self) -> bool:
        """Verifica si Docker está disponible."""
        try:
            subprocess.run(["docker", "--version"], capture_output=True)
            return True
        except:
            return False
            
    def execute_command(self, command: Union[str, List[str]], shell: bool = False, **kwargs) -> Dict:
        """
        Ejecuta un comando con capacidades avanzadas.
        
        Args:
            command: Comando a ejecutar
            shell: Si se debe usar shell
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con el resultado
        """
        try:
            # Convertir comando a lista si es string
            if isinstance(command, str):
                command = command.split()
                
            # Configurar proceso
            process = subprocess.Popen(
                command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=shell,
                **kwargs
            )
            
            # Capturar salida en tiempo real
            stdout_lines = []
            stderr_lines = []
            
            while True:
                stdout_line = process.stdout.readline()
                stderr_line = process.stderr.readline()
                
                if stdout_line:
                    self.logger.info(stdout_line.strip())
                    stdout_lines.append(stdout_line)
                    
                if stderr_line:
                    self.logger.error(stderr_line.strip())
                    stderr_lines.append(stderr_line)
                    
                if not stdout_line and not stderr_line and process.poll() is not None:
                    break
                    
            return {
                "success": process.returncode == 0,
                "output": "".join(stdout_lines),
                "error": "".join(stderr_lines),
                "return_code": process.returncode
            }
        except Exception as e:
            self.logger.error(f"Error ejecutando comando: {e}")
            return {
                "success": False,
                "error": str(e),
                "return_code": -1
            }
            
    def monitor_resources(self) -> Dict:
        """Monitorea recursos del sistema."""
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "network": psutil.net_io_counters()._asdict()
        }
        
    def create_container(self, image: str, **kwargs) -> Dict:
        """
        Crea un contenedor Docker.
        
        Args:
            image: Imagen Docker
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con información del contenedor
        """
        if not self.docker_client:
            return {"success": False, "error": "Docker no está disponible"}
            
        try:
            container = self.docker_client.containers.run(
                image,
                detach=True,
                **kwargs
            )
            return {
                "success": True,
                "container_id": container.id,
                "status": container.status
            }
        except Exception as e:
            self.logger.error(f"Error creando contenedor: {e}")
            return {"success": False, "error": str(e)}
            
    def setup_development_environment(self, requirements: Dict) -> Dict:
        """
        Configura un entorno de desarrollo completo.
        
        Args:
            requirements: Requerimientos del entorno
            
        Returns:
            Dict con el resultado
        """
        try:
            results = {}
            
            # Crear entorno virtual
            if requirements.get("virtual_env"):
                venv_path = self.working_dir / "venv"
                results["venv"] = self.execute_command(
                    [sys.executable, "-m", "venv", str(venv_path)]
                )
                
            # Clonar repositorios
            if "repositories" in requirements and DOCKER_AVAILABLE:
                results["repos"] = {}
                for repo in requirements["repositories"]:
                    repo_path = self.working_dir / repo["name"]
                    git.Repo.clone_from(repo["url"], repo_path)
                    results["repos"][repo["name"]] = {"success": True}
                    
            # Instalar dependencias
            if "dependencies" in requirements:
                results["dependencies"] = {}
                pip_command = [
                    str(venv_path / "Scripts" / "pip") if requirements.get("virtual_env")
                    else "pip"
                ]
                for dep in requirements["dependencies"]:
                    results["dependencies"][dep] = self.execute_command(
                        [*pip_command, "install", dep]
                    )
                    
            # Configurar Docker
            if "containers" in requirements and self.docker_client:
                results["containers"] = {}
                for container in requirements["containers"]:
                    results["containers"][container["name"]] = self.create_container(**container)
                    
            return {"success": True, "results": results}
        except Exception as e:
            self.logger.error(f"Error configurando entorno: {e}")
            return {"success": False, "error": str(e)}
            
    def parallel_execute(self, commands: List[Union[str, List[str]]], mode: str = "thread") -> List[Dict]:
        """
        Ejecuta comandos en paralelo.
        
        Args:
            commands: Lista de comandos
            mode: Modo de ejecución ('thread' o 'process')
            
        Returns:
            Lista de resultados
        """
        executor = self.thread_pool if mode == "thread" else self.process_pool
        return list(executor.map(self.execute_command, commands))
        
    def backup_project(self, backup_dir: Optional[Path] = None) -> Dict:
        """
        Crea un backup completo del proyecto.
        
        Args:
            backup_dir: Directorio para el backup
            
        Returns:
            Dict con el resultado
        """
        try:
            # Crear directorio de backup
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = backup_dir or Path("backups")
            backup_path = backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivos
            shutil.copytree(
                self.working_dir,
                backup_path / self.working_dir.name,
                ignore=shutil.ignore_patterns("venv", "node_modules", "__pycache__", "*.pyc")
            )
            
            # Crear manifest
            manifest = {
                "timestamp": timestamp,
                "original_path": str(self.working_dir),
                "files": [],
                "resources": self.monitor_resources()
            }
            
            # Registrar archivos
            for file in backup_path.rglob("*"):
                if file.is_file():
                    manifest["files"].append({
                        "path": str(file.relative_to(backup_path)),
                        "size": file.stat().st_size,
                        "modified": datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                    })
                    
            # Guardar manifest
            with open(backup_path / "manifest.json", "w") as f:
                json.dump(manifest, f, indent=4)
                
            return {
                "success": True,
                "backup_path": str(backup_path),
                "manifest": manifest
            }
        except Exception as e:
            self.logger.error(f"Error creando backup: {e}")
            return {"success": False, "error": str(e)}
            
    def cleanup(self):
        """Limpia recursos del sistema."""
        self.thread_pool.shutdown()
        self.process_pool.shutdown()
        if self.docker_client:
            self.docker_client.close()
