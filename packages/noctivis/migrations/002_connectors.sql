CREATE TABLE connectors (
    id text PRIMARY KEY,
    kind text NOT NULL CHECK (kind = 'llm'),
    name text NOT NULL CHECK (char_length(name) BETWEEN 1 AND 200),
    description text NOT NULL DEFAULT '',
    enabled boolean NOT NULL DEFAULT true,
    is_default boolean NOT NULL DEFAULT false,
    config jsonb NOT NULL,
    last_checked_at timestamptz,
    last_status text NOT NULL DEFAULT 'unknown' CHECK (last_status IN ('unknown', 'connected', 'unreachable', 'error'))
);

CREATE UNIQUE INDEX connectors_one_default ON connectors (kind) WHERE is_default;
