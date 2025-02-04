"""
Utilidad para ejecutar comandos en la terminal con capacidades avanzadas.
"""
from typing import Dict, List, Optional, Union
from pathlib import Path
from .system_manager import SystemManager
import os
import subprocess
import sys

class CommandExecutor:
    """Clase para ejecutar comandos en la terminal con capacidades avanzadas."""
    
    def __init__(self, working_dir: Optional[Path] = None):
        """
        Inicializa el ejecutor de comandos.
        
        Args:
            working_dir: Directorio de trabajo opcional
        """
        self.system = SystemManager(working_dir)
        self.working_dir = working_dir or Path.cwd()
        
    def execute(self, command: Union[str, List[str]], capture_output: bool = True, shell: bool = False) -> Dict:
        """
        Ejecuta un comando en la terminal.
        
        Args:
            command: Comando a ejecutar
            capture_output: Si se debe capturar la salida
            shell: Si se debe usar shell
            
        Returns:
            Dict con el resultado de la ejecución
        """
        return self.system.execute_command(command, shell=shell)
        
    def install_package(self, package: str) -> Dict:
        """
        Instala un paquete usando pip.
        
        Args:
            package: Nombre del paquete
            
        Returns:
            Dict con el resultado de la instalación
        """
        python_exe = str(self.working_dir / "venv" / "Scripts" / "python.exe")
        if os.path.exists(python_exe):
            return self.system.execute_command([python_exe, "-m", "pip", "install", package])
        else:
            return self.system.execute_command(["pip", "install", package])
        
    def run_python_script(self, script_path: Path, args: str = "") -> Dict:
        """
        Ejecuta un script de Python.
        
        Args:
            script_path: Ruta al script
            args: Argumentos adicionales
            
        Returns:
            Dict con el resultado de la ejecución
        """
        python_exe = str(self.working_dir / "venv" / "Scripts" / "python.exe")
        if os.path.exists(python_exe):
            return self.system.execute_command([python_exe, str(script_path)] + (args.split() if args else []))
        else:
            return self.system.execute_command(["python", str(script_path)] + (args.split() if args else []))
        
    def run_tests(self, test_path: Optional[Path] = None) -> Dict:
        """
        Ejecuta tests usando pytest.
        
        Args:
            test_path: Ruta opcional a los tests específicos
            
        Returns:
            Dict con el resultado de los tests
        """
        python_exe = str(self.working_dir / "venv" / "Scripts" / "python.exe")
        command = [python_exe, "-m", "pytest"] if os.path.exists(python_exe) else ["pytest"]
        if test_path:
            command.append(str(test_path))
        command.append("-v")
        return self.system.execute_command(command)
        
    def create_virtual_env(self, env_name: str = "venv") -> Dict:
        """
        Crea un entorno virtual.
        
        Args:
            env_name: Nombre del entorno virtual
            
        Returns:
            Dict con el resultado de la creación
        """
        return self.system.execute_command([sys.executable, "-m", "venv", env_name])
        
    def activate_virtual_env(self) -> Dict:
        """
        Activa el entorno virtual.
        
        Returns:
            Dict con el resultado de la activación
        """
        if os.name == "nt":  # Windows
            activate_script = str(self.working_dir / "venv" / "Scripts" / "activate.bat")
            if os.path.exists(activate_script):
                # En Windows, necesitamos usar cmd.exe para activar el entorno
                command = [activate_script]
                result = self.system.execute_command(command)
                
                # Actualizar variables de entorno
                if result["success"]:
                    # Obtener las variables de entorno actualizadas
                    env_result = self.system.execute_command("set")
                    if env_result["success"]:
                        for line in env_result["output"].splitlines():
                            if "=" in line:
                                key, value = line.split("=", 1)
                                os.environ[key] = value
                                
                return result
            else:
                return {
                    "success": False,
                    "error": "No se encontró el script de activación",
                    "return_code": -1
                }
        else:  # Unix/Linux
            activate_script = str(self.working_dir / "venv" / "bin" / "activate")
            if os.path.exists(activate_script):
                return self.system.execute_command(f"source {activate_script}", shell=True)
            else:
                return {
                    "success": False,
                    "error": "No se encontró el script de activación",
                    "return_code": -1
                }
            
    def setup_development_environment(self, requirements: Dict) -> Dict:
        """
        Configura un entorno de desarrollo completo.
        
        Args:
            requirements: Requerimientos del entorno
            
        Returns:
            Dict con el resultado
        """
        return self.system.setup_development_environment(requirements)
        
    def run_parallel_commands(self, commands: List[Union[str, List[str]]], mode: str = "thread") -> List[Dict]:
        """
        Ejecuta comandos en paralelo.
        
        Args:
            commands: Lista de comandos
            mode: Modo de ejecución ('thread' o 'process')
            
        Returns:
            Lista de resultados
        """
        return self.system.parallel_execute(commands, mode)
        
    def create_container(self, image: str, **kwargs) -> Dict:
        """
        Crea un contenedor Docker.
        
        Args:
            image: Imagen Docker
            **kwargs: Argumentos adicionales
            
        Returns:
            Dict con información del contenedor
        """
        return self.system.create_container(image, **kwargs)
        
    def monitor_system(self) -> Dict:
        """
        Monitorea recursos del sistema.
        
        Returns:
            Dict con información de recursos
        """
        return self.system.monitor_resources()
        
    def backup_project(self, backup_dir: Optional[Path] = None) -> Dict:
        """
        Crea un backup completo del proyecto.
        
        Args:
            backup_dir: Directorio para el backup
            
        Returns:
            Dict con el resultado
        """
        return self.system.backup_project(backup_dir)
        
    def cleanup(self):
        """Limpia recursos del sistema."""
        self.system.cleanup()
