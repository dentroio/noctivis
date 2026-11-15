CREATE TABLE analysis_jobs (
    id text PRIMARY KEY,
    investigation_id text NOT NULL REFERENCES investigations (id),
    binary_id text NOT NULL REFERENCES binaries (id),
    sha256 text NOT NULL CHECK (char_length(sha256) = 64),
    status text NOT NULL CHECK (status IN ('queued', 'running', 'completed', 'failed')),
    error text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    started_at timestamptz,
    finished_at timestamptz
);

CREATE UNIQUE INDEX analysis_jobs_one_open ON analysis_jobs (investigation_id) WHERE status IN ('queued', 'running');

CREATE TABLE evidence (
    id text PRIMARY KEY,
    investigation_id text NOT NULL REFERENCES investigations (id),
    binary_id text NOT NULL REFERENCES binaries (id),
    job_id text NOT NULL REFERENCES analysis_jobs (id),
    sha256 text NOT NULL CHECK (char_length(sha256) = 64),
    tool text NOT NULL CHECK (tool = 'ghidra'),
    tool_version text NOT NULL CHECK (char_length(tool_version) BETWEEN 1 AND 80),
    kind text NOT NULL CHECK (kind IN ('function_inventory', 'decompilation')),
    body jsonb NOT NULL
);
