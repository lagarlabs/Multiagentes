# Empresa Virtual de Desarrollo de Software

Este proyecto implementa una empresa virtual compuesta por agentes de IA especializados que colaboran de forma autónoma para desarrollar proyectos de software completos, utilizando la biblioteca Agno y modelos de lenguaje avanzados.

## Características

- **Empresa Virtual Completa**: Simula una empresa de desarrollo con especialistas en diferentes áreas
- **Agentes Especializados**: Coordinador, analista de mercado, desarrolladores frontend/backend y QA
- **Flujo de Desarrollo Completo**: Desde análisis de requerimientos hasta entrega final
- **Análisis de Mercado**: Evaluación de tendencias y competitividad del proyecto
- **Desarrollo Paralelo**: Implementación simultánea de backend y frontend
- **Generación de Informes**: Reportes detallados del proyecto para cada fase
- **Interfaz Interactiva**: Monitoreo en tiempo real del progreso utilizando Rich

## Equipo de Agentes

- **Coordinador de Proyecto**: Gestiona todo el proceso de desarrollo y asigna tareas
- **Analista de Mercado**: Evalúa tendencias, competidores y oportunidades
- **Investigador Técnico**: Investiga tecnologías y mejores prácticas actuales
- **Desarrollador Backend**: Implementa APIs, bases de datos y lógica de negocio
- **Desarrollador Frontend**: Crea interfaces de usuario y componentes interactivos
- **Tester y Analista de Calidad**: Verifica la calidad del código y sugiere mejoras

## Fases del Desarrollo

La empresa virtual sigue un proceso de desarrollo estructurado en seis fases:

1. **Investigación y Análisis**: Análisis de requerimientos y tecnologías recomendadas
2. **Diseño de Arquitectura**: Diseño de componentes y estructura del sistema
3. **Análisis de Mercado**: Evaluación de competidores y recomendaciones estratégicas
4. **Implementación**: Desarrollo paralelo de componentes frontend y backend
5. **Testing y QA**: Verificación de calidad y refactorización según feedback
6. **Ajustes Finales**: Modificaciones basadas en análisis de mercado y testing

## Requisitos

- Python 3.8+
- OpenAI API Key
- DeepSeek API Key
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd empresa_virtual
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
# Editar .env y agregar tus API keys para OpenAI y DeepSeek
```

## Uso

Para iniciar la empresa virtual:

```bash
python main.py
```

Esto iniciará una interfaz interactiva donde podrás:

1. Describir tu proyecto en detalle
2. Observar el progreso en tiempo real mientras los agentes trabajan
3. Revisar el informe final con la arquitectura, componentes y recomendaciones
4. Encontrar los archivos de salida en la carpeta `projects/[timestamp]`

El sistema funciona de forma autónoma, con los agentes especializados colaborando entre sí para completar todas las fases del desarrollo.

## Estructura del Proyecto

```
empresa_virtual/
├── agents/                    # Agentes especializados
│   ├── coordinator_agent.py   # Agente coordinador principal
│   ├── market_analysis_agent.py # Analista de mercado
│   ├── frontend_programmer_agent.py # Desarrollador frontend
│   ├── backend_programmer_agent.py # Desarrollador backend
│   └── qa_agent.py            # Agente de control de calidad
├── config/                    # Configuración del sistema
├── docs/                      # Documentación generada
├── logs/                      # Registros del sistema
├── output/                    # Salidas temporales
├── projects/                  # Proyectos completados
├── utils/                     # Utilidades compartidas
├── .env.example               # Ejemplo de configuración
├── main.py                    # Punto de entrada principal
├── README.md                  # Esta documentación
└── requirements.txt           # Dependencias del proyecto
```

## Configuración

Las siguientes variables pueden ser configuradas en el archivo `.env`:

- `OPENAI_API_KEY`: Tu API key de OpenAI
- `DEEPSEEK_API_KEY`: Tu API key de DeepSeek
- `LOG_LEVEL`: Nivel de logging (default: INFO)
- `DEFAULT_MODEL`: Modelo de OpenAI a usar (default: gpt-4-turbo)
- `REASONING_MODEL`: Modelo de DeepSeek a usar (default: deepseek-chat)
- `MAX_RETRIES`: Número máximo de reintentos (default: 3)
- `TIMEOUT_SECONDS`: Tiempo máximo de espera (default: 300)
- `TEMPERATURE`: Temperatura para la generación (default: 0.7)
- `MAX_TOKENS`: Máximo de tokens por respuesta (default: 4000)

## Contribuir

1. Fork el repositorio
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo `LICENSE` para más detalles.