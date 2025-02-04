# Sistema Multi-Agentes para Desarrollo de Software

Este proyecto implementa un sistema multi-agentes para el desarrollo automatizado de software, utilizando la biblioteca Agno y el modelo de lenguaje Deepseek.

## Características

- **Coordinador**: Agente que analiza proyectos y divide el trabajo en tareas específicas
- **Programadores**: Agentes que implementan las tareas asignadas
- **QA**: Agente que revisa la calidad del código y la documentación
- **Comunicación Asíncrona**: Los agentes se comunican de forma asíncrona para maximizar la eficiencia
- **Monitoreo en Tiempo Real**: Sistema de monitoreo del progreso de las tareas
- **Documentación Automática**: Generación automática de documentación en español
- **Pruebas Unitarias**: Generación automática de pruebas unitarias

## Requisitos

- Python 3.8+
- Deepseek API Key
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd empresa_multiagentes
```

2. Crear y activar un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env y agregar tu DEEPSEEK_API_KEY
```

## Uso

1. Iniciar el sistema:
```bash
python main.py
```

2. El sistema incluye un ejemplo que:
   - Registra tres programadores con diferentes habilidades
   - Procesa un proyecto de ejemplo
   - Muestra el estado del sistema

3. Para usar en tu propio proyecto:
```python
from main import MultiAgentSystem

# Crear el sistema
system = MultiAgentSystem()

# Registrar programadores
system.register_programmer("prog1", ["python", "web", "database"])
system.register_programmer("prog2", ["python", "ai", "testing"])

# Procesar un proyecto
result = await system.process_project("""
    Descripción detallada del proyecto...
""")

# Obtener estado del sistema
status = await system.get_system_status()
```

## Estructura del Proyecto

```
empresa_multiagentes/
├── agents/
│   ├── coordinator_agent.py
│   ├── programmer_agent.py
│   └── qa_agent.py
├── config/
│   └── settings.py
├── logs/
├── .env.example
├── main.py
├── README.md
└── requirements.txt
```

## Configuración

Las siguientes variables pueden ser configuradas en el archivo `.env`:

- `DEEPSEEK_API_KEY`: Tu API key de Deepseek
- `LOG_LEVEL`: Nivel de logging (default: INFO)
- `MAX_RETRIES`: Número máximo de reintentos (default: 3)
- `TIMEOUT_SECONDS`: Tiempo máximo de espera (default: 300)
- `DEFAULT_MODEL`: Modelo de Deepseek a usar (default: deepseek-chat)
- `TEMPERATURE`: Temperatura para la generación (default: 0.7)
- `MAX_TOKENS`: Máximo de tokens por respuesta (default: 2000)

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo `LICENSE` para más detalles.
