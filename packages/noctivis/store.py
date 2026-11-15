"""PostgreSQL records for classified samples and investigations."""

import threading
from pathlib import Path
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from noctivis.connectors import validate_llm_config
from noctivis.models import Investigation


class AnalysisBusy(Exception):
    """An investigation already has a queued, running, or completed analysis job."""

MIGRATIONS = Path(__file__).parent / "migrations"
_ADVISORY_LOCK = 0x4E6F6374


def _statements(script: str) -> list[str]:
    return [part.strip() for part in script.split(";") if part.strip()]


class RecordStore:
    def __init__(self, url: str):
        self._lock = threading.Lock()
        try:
            self._conn = psycopg.connect(url, autocommit=False, row_factory=dict_row)
        except psycopg.OperationalError as exc:
            raise RuntimeError(
                "Could not connect to the NOCTIVIS database. Check NOCTIVIS_DATABASE_URL and that PostgreSQL is running on loopback."
            ) from exc
        self._migrate()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @property
    def closed(self) -> bool:
        return self._conn.closed

    def _migrate(self) -> None:
        with self._lock:
            self._conn.execute("SELECT pg_advisory_lock(%s)", (_ADVISORY_LOCK,))
            try:
                self._conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS schema_migrations (
                        version text PRIMARY KEY,
                        applied_at timestamptz NOT NULL DEFAULT now()
                    )
                    """
                )
                applied = {row["version"] for row in self._conn.execute("SELECT version FROM schema_migrations").fetchall()}
                for path in sorted(MIGRATIONS.glob("*.sql")):
                    if path.name in applied:
                        continue
                    for statement in _statements(path.read_text()):
                        self._conn.execute(statement)
                    self._conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.name,))
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise
            finally:
                self._conn.execute("SELECT pg_advisory_unlock(%s)", (_ADVISORY_LOCK,))
                self._conn.commit()

    def _write(self, query: str, params: tuple):
        self._transaction([(query, params)])

    def _transaction(self, statements: list[tuple[str, tuple]]):
        with self._lock:
            try:
                for query, params in statements:
                    self._conn.execute(query, params)
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def _read(self, query: str, params: tuple = ()):
        with self._lock:
            try:
                rows = self._conn.execute(query, params).fetchall()
                self._conn.rollback()
                return rows
            except Exception:
                self._conn.rollback()
                raise

    def save_binary(self, record: dict) -> dict:
        self._write(
            """
            INSERT INTO binaries (id, sha256, label, format, size_bytes)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE
            SET label = EXCLUDED.label, format = EXCLUDED.format, size_bytes = EXCLUDED.size_bytes
            """,
            (record["id"], record["sha256"], record["label"], record["format"], record["size_bytes"]),
        )
        return record

    def list_binaries(self) -> list[dict]:
        rows = self._read("SELECT id, sha256, label, format, size_bytes FROM binaries ORDER BY id")
        return [dict(row) for row in rows]

    def has_binary(self, binary_id: str) -> bool:
        rows = self._read("SELECT id FROM binaries WHERE id = %s", (binary_id,))
        return bool(rows)

    def save_investigation(self, investigation: Investigation) -> Investigation:
        self._write(
            """
            INSERT INTO investigations (
                id, binary_id, objective, status, max_tool_calls, dynamic_execution, findings
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                investigation.id,
                investigation.binary_id,
                investigation.objective,
                investigation.status.value,
                investigation.max_tool_calls,
                investigation.dynamic_execution,
                Jsonb(investigation.findings),
            ),
        )
        return investigation

    def list_investigations(self) -> list[Investigation]:
        rows = self._read(
            """
            SELECT id, binary_id, objective, status, max_tool_calls, dynamic_execution, findings
            FROM investigations
            ORDER BY id
            """
        )
        return [self._investigation(row) for row in rows]

    def get_investigation(self, investigation_id: str) -> Investigation | None:
        rows = self._read(
            """
            SELECT id, binary_id, objective, status, max_tool_calls, dynamic_execution, findings
            FROM investigations
            WHERE id = %s
            """,
            (investigation_id,),
        )
        if not rows:
            return None
        return self._investigation(rows[0])

    def get_binary(self, binary_id: str) -> dict | None:
        rows = self._read(
            "SELECT id, sha256, label, format, size_bytes FROM binaries WHERE id = %s",
            (binary_id,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def enqueue_analysis(self, job: dict) -> dict:
        with self._lock:
            try:
                existing = self._conn.execute(
                    """
                    SELECT status FROM analysis_jobs
                    WHERE investigation_id = %s AND status IN ('queued', 'running', 'completed')
                    LIMIT 1
                    """,
                    (job["investigation_id"],),
                ).fetchone()
                if existing is not None:
                    self._conn.rollback()
                    raise AnalysisBusy(existing["status"])
                self._conn.execute(
                    """
                    INSERT INTO analysis_jobs (id, investigation_id, binary_id, sha256, status)
                    VALUES (%s, %s, %s, %s, 'queued')
                    """,
                    (job["id"], job["investigation_id"], job["binary_id"], job["sha256"]),
                )
                self._conn.execute(
                    "UPDATE investigations SET status = 'queued' WHERE id = %s",
                    (job["investigation_id"],),
                )
                self._conn.commit()
            except AnalysisBusy:
                raise
            except psycopg.errors.UniqueViolation as exc:
                self._conn.rollback()
                raise AnalysisBusy("queued") from exc
            except Exception:
                self._conn.rollback()
                raise
        stored = self.latest_analysis_job(job["investigation_id"])
        if stored is None:
            raise RuntimeError("analysis job was not stored")
        return stored

    def latest_analysis_job(self, investigation_id: str) -> dict | None:
        rows = self._read(
            """
            SELECT id, investigation_id, binary_id, sha256, status, error
            FROM analysis_jobs
            WHERE investigation_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (investigation_id,),
        )
        if not rows:
            return None
        return dict(rows[0])

    def claim_analysis_job(self) -> dict | None:
        with self._lock:
            try:
                row = self._conn.execute(
                    """
                    SELECT id, investigation_id, binary_id, sha256
                    FROM analysis_jobs
                    WHERE status = 'queued'
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                    """
                ).fetchone()
                if row is None:
                    self._conn.rollback()
                    return None
                self._conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = 'running', started_at = now(), error = ''
                    WHERE id = %s
                    """,
                    (row["id"],),
                )
                self._conn.execute(
                    "UPDATE investigations SET status = 'running' WHERE id = %s",
                    (row["investigation_id"],),
                )
                self._conn.commit()
                return dict(row)
            except Exception:
                self._conn.rollback()
                raise

    def complete_analysis_job(self, job: dict, tool_version: str, inventory: dict, decompilation: dict) -> None:
        with self._lock:
            try:
                for kind, body in (("function_inventory", inventory), ("decompilation", decompilation)):
                    self._conn.execute(
                        """
                        INSERT INTO evidence (
                            id, investigation_id, binary_id, job_id, sha256, tool, tool_version, kind, body
                        )
                        VALUES (%s, %s, %s, %s, %s, 'ghidra', %s, %s, %s)
                        """,
                        (
                            str(uuid4()),
                            job["investigation_id"],
                            job["binary_id"],
                            job["id"],
                            job["sha256"],
                            tool_version,
                            kind,
                            Jsonb(body),
                        ),
                    )
                updated = self._conn.execute(
                    """
                    UPDATE analysis_jobs
                    SET status = 'completed', finished_at = now(), error = ''
                    WHERE id = %s AND status = 'running'
                    """,
                    (job["id"],),
                )
                if updated.rowcount != 1:
                    raise RuntimeError("analysis job is no longer running")
                self._conn.execute(
                    "UPDATE investigations SET status = 'completed' WHERE id = %s",
                    (job["investigation_id"],),
                )
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def fail_analysis_job(self, job_id: str, investigation_id: str, message: str) -> None:
        self._transaction(
            [
                (
                    """
                    UPDATE analysis_jobs
                    SET status = 'failed', error = %s, finished_at = now()
                    WHERE id = %s AND status = 'running'
                    """,
                    (message[:500], job_id),
                ),
                (
                    "UPDATE investigations SET status = 'failed' WHERE id = %s",
                    (investigation_id,),
                ),
            ]
        )

    def list_evidence(self, investigation_id: str) -> list[dict]:
        rows = self._read(
            """
            SELECT id, investigation_id, binary_id, job_id, sha256, tool, tool_version, kind, body
            FROM evidence
            WHERE investigation_id = %s
            ORDER BY kind
            """,
            (investigation_id,),
        )
        return [dict(row) for row in rows]

    def list_connectors(self, kind: str) -> list[dict]:
        rows = self._read(
            """
            SELECT id, kind, name, description, enabled, is_default, config, last_checked_at, last_status
            FROM connectors
            WHERE kind = %s
            ORDER BY is_default DESC, name
            """,
            (kind,),
        )
        return [self._connector(row) for row in rows]

    def get_connector(self, connector_id: str) -> dict | None:
        rows = self._read(
            """
            SELECT id, kind, name, description, enabled, is_default, config, last_checked_at, last_status
            FROM connectors
            WHERE id = %s
            """,
            (connector_id,),
        )
        if not rows:
            return None
        return self._connector(rows[0])

    def insert_connector(self, record: dict) -> dict:
        config = validate_llm_config(record["config"])
        statements = []
        if record["is_default"]:
            statements.append(
                ("UPDATE connectors SET is_default = false WHERE kind = %s AND is_default", (record["kind"],))
            )
        statements.append(
            (
                """
                INSERT INTO connectors (id, kind, name, description, enabled, is_default, config)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    record["id"],
                    record["kind"],
                    record["name"],
                    record["description"],
                    record["enabled"],
                    record["is_default"],
                    Jsonb(config),
                ),
            )
        )
        self._transaction(statements)
        stored = self.get_connector(record["id"])
        if stored is None:
            raise RuntimeError("connector was not stored")
        return stored

    def update_connector(self, connector_id: str, changes: dict) -> dict | None:
        current = self.get_connector(connector_id)
        if current is None:
            return None
        config = validate_llm_config(changes["config"]) if "config" in changes else current["config"]
        name = changes.get("name", current["name"])
        description = changes.get("description", current["description"])
        enabled = changes.get("enabled", current["enabled"])
        is_default = changes.get("is_default", current["is_default"])
        statements = []
        if is_default:
            statements.append(
                (
                    "UPDATE connectors SET is_default = false WHERE kind = %s AND id <> %s AND is_default",
                    (current["kind"], connector_id),
                )
            )
        statements.append(
            (
                """
                UPDATE connectors
                SET name = %s, description = %s, enabled = %s, is_default = %s, config = %s
                WHERE id = %s
                """,
                (name, description, enabled, is_default, Jsonb(config), connector_id),
            )
        )
        self._transaction(statements)
        return self.get_connector(connector_id)

    def mark_connector_checked(self, connector_id: str, status: str) -> None:
        self._write(
            """
            UPDATE connectors
            SET last_checked_at = now(), last_status = %s
            WHERE id = %s
            """,
            (status, connector_id),
        )

    def delete_connector(self, connector_id: str) -> bool:
        current = self.get_connector(connector_id)
        if current is None:
            return False
        self._write("DELETE FROM connectors WHERE id = %s", (connector_id,))
        return True

    @staticmethod
    def _connector(row: dict) -> dict:
        record = dict(row)
        checked = record.get("last_checked_at")
        if checked is not None:
            record["last_checked_at"] = checked.isoformat()
        return record

    @staticmethod
    def _investigation(row: dict) -> Investigation:
        return Investigation(
            id=row["id"],
            binary_id=row["binary_id"],
            objective=row["objective"],
            status=row["status"],
            max_tool_calls=row["max_tool_calls"],
            dynamic_execution=row["dynamic_execution"],
            findings=row["findings"] or [],
        )
