"""
Utilidades para la ejecución de comandos del sistema.
"""

import os
import asyncio
import platform
import logging
from pathlib import Path
from typing import List, Tuple, Optional

async def execute_command(command: str, cwd: str = None) -> Tuple[str, str, int]:
    """
    Ejecuta un comando del sistema de forma asíncrona y multiplataforma.
    
    Args:
        command: Comando a ejecutar
        cwd: Directorio de trabajo
        
    Returns:
        Tupla con (stdout, stderr, código_retorno)
    """
    logging.info(f"Ejecutando comando: {command}")
    
    # Adaptar comando según plataforma
    system = platform.system()
    shell = True
    if system == "Windows":
        # En Windows, algunos comandos necesitan ser ejecutados a través de cmd
        if any(cmd in command for cmd in ["npm", "yarn", "pip"]):
            command = f"cmd /c {command}"
    elif system == "Linux" or system == "Darwin":  # Darwin es macOS
        # En Unix, podemos usar bash directamente
        if command.startswith("cmd /c"):
            command = command[7:]  # Quitar "cmd /c "
    
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            shell=shell
        )
        
        stdout, stderr = await process.communicate()
        
        stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
        stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
        
        if stdout_text:
            logging.info(f"Salida: {stdout_text[:100]}...")
        if stderr_text:
            logging.warning(f"Error: {stderr_text[:100]}...")
        
        return stdout_text, stderr_text, process.returncode
    except Exception as e:
        logging.error(f"Error al ejecutar comando '{command}': {str(e)}")
        return "", str(e), 1

async def create_file(path: str, content: str, base_dir: str = None) -> bool:
    """
    Crea un archivo con el contenido especificado.
    
    Args:
        path: Ruta relativa del archivo
        content: Contenido a escribir
        base_dir: Directorio base (por defecto current working directory)
        
    Returns:
        True si se creó exitosamente, False en caso contrario
    """
    try:
        # Normalizar path según plataforma
        path = Path(path)
        if base_dir:
            full_path = Path(base_dir) / path
        else:
            full_path = Path.cwd() / path
        
        # Crear directorio si no existe
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir contenido
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        logging.info(f"Archivo creado: {full_path}")
        return True
    except Exception as e:
        logging.error(f"Error al crear archivo '{path}': {str(e)}")
        return False

async def create_directory(path: str, base_dir: str = None) -> bool:
    """
    Crea un directorio.
    
    Args:
        path: Ruta relativa del directorio
        base_dir: Directorio base (por defecto current working directory)
        
    Returns:
        True si se creó exitosamente, False en caso contrario
    """
    try:
        # Normalizar path según plataforma
        path = Path(path)
        if base_dir:
            full_path = Path(base_dir) / path
        else:
            full_path = Path.cwd() / path
        
        # Crear directorio
        full_path.mkdir(parents=True, exist_ok=True)
        
        logging.info(f"Directorio creado: {full_path}")
        return True
    except Exception as e:
        logging.error(f"Error al crear directorio '{path}': {str(e)}")
        return False

async def process_agent_actions(actions: List[str], cwd: str) -> List[Tuple[str, bool]]:
    """
    Procesa las acciones ejecutadas por un agente.
    
    Args:
        actions: Lista de acciones a ejecutar
        cwd: Directorio de trabajo
        
    Returns:
        Lista de tuplas (acción, éxito)
    """
    results = []
    
    for action in actions:
        success = False
        try:
            if action.startswith("create_file:"):
                # Formato: create_file:path:content
                parts = action.split(":", 2)
                if len(parts) >= 3:
                    path, content = parts[1], parts[2]
                    success = await create_file(path, content, cwd)
                else:
                    logging.error(f"Formato incorrecto para create_file: {action}")
            
            elif action.startswith("run_command:"):
                # Formato: run_command:command
                command = action.split(":", 1)[1]
                _, stderr, code = await execute_command(command, cwd)
                success = code == 0
            
            elif action.startswith("mkdir:"):
                # Formato: mkdir:path
                path = action.split(":", 1)[1]
                success = await create_directory(path, cwd)
            
            else:
                logging.warning(f"Acción no reconocida: {action}")
                
        except Exception as e:
            logging.error(f"Error al procesar acción {action}: {str(e)}")
            success = False
        
        results.append((action, success))
    
    return results