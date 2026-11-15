CREATE TABLE binaries (
    id text PRIMARY KEY,
    sha256 text NOT NULL,
    label text NOT NULL,
    format text NOT NULL,
    size_bytes integer NOT NULL CHECK (size_bytes >= 0)
);

CREATE TABLE investigations (
    id text PRIMARY KEY,
    binary_id text NOT NULL REFERENCES binaries (id),
    objective text NOT NULL CHECK (char_length(objective) BETWEEN 3 AND 2000),
    status text NOT NULL CHECK (status IN ('created', 'queued', 'running', 'completed', 'failed', 'cancelled')),
    max_tool_calls integer NOT NULL CHECK (max_tool_calls BETWEEN 1 AND 500),
    dynamic_execution boolean NOT NULL DEFAULT false,
    findings jsonb NOT NULL DEFAULT '[]'::jsonb
);
