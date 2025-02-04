-- Habilitar la extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Crear tabla para el conocimiento del proyecto
CREATE TABLE IF NOT EXISTS project_knowledge (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    embedding vector(1536),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índice para búsqueda por similitud
CREATE INDEX IF NOT EXISTS project_knowledge_embedding_idx ON project_knowledge USING ivfflat (embedding vector_cosine_ops);

-- Crear tabla para sesiones de agentes
CREATE TABLE IF NOT EXISTS agent_sessions (
    id SERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    messages JSONB,
    state JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para sesiones
CREATE INDEX IF NOT EXISTS agent_sessions_session_id_idx ON agent_sessions(session_id);
CREATE INDEX IF NOT EXISTS agent_sessions_agent_id_idx ON agent_sessions(agent_id);
