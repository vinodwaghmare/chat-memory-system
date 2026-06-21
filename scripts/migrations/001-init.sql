-- 001-init.sql — Chat Memory System schema
-- Idempotent: safe to run multiple times.

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- =========================================================================
-- memories — the core record from the HTML design §7.4
-- =========================================================================
CREATE TABLE IF NOT EXISTS memories (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL,
    type                TEXT CHECK (type IN ('episodic', 'semantic', 'procedural')),
    content             TEXT NOT NULL,
    embedding           VECTOR(1536),
    importance          INT DEFAULT 5,
    confidence          REAL DEFAULT 0.8,
    source              JSONB DEFAULT '{}',
    weight              REAL DEFAULT 1.0,
    reinforcement_count INT DEFAULT 0,
    archived            BOOLEAN DEFAULT false,
    deleted             BOOLEAN DEFAULT false,
    deleted_at          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now(),
    updated_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_memories_user_id ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_user_type ON memories(user_id, type);
CREATE INDEX IF NOT EXISTS idx_memories_content_trgm ON memories USING gin (content gin_trgm_ops);

-- Invariant 1: row-level security ensures user isolation
ALTER TABLE memories ENABLE ROW LEVEL SECURITY;

-- =========================================================================
-- memory_edges — graph links between memories (v2 feature, schema ready)
-- =========================================================================
CREATE TABLE IF NOT EXISTS memory_edges (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_memory_id  UUID NOT NULL REFERENCES memories(id),
    to_memory_id    UUID NOT NULL REFERENCES memories(id),
    relation        TEXT NOT NULL,
    user_id         UUID NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edges_user ON memory_edges(user_id);
CREATE INDEX IF NOT EXISTS idx_edges_from ON memory_edges(from_memory_id);

-- =========================================================================
-- audit_log — append-only, supports Invariant 4 (provenance)
-- =========================================================================
CREATE TABLE IF NOT EXISTS audit_log (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL,
    action      TEXT NOT NULL,
    memory_id   UUID,
    details     JSONB,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
