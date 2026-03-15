from pathlib import Path
import sqlite3

from app.schemas.chat import ChatMessage


class AgentSessionStore:
    def __init__(self, database_path: str, max_messages: int) -> None:
        self.database_path = Path(database_path)
        self.max_messages = max_messages
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def load_history(self, session_id: str) -> list[ChatMessage]:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                SELECT role, content
                FROM (
                    SELECT role, content, created_at, rowid
                    FROM agent_session_messages
                    WHERE session_id = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT ?
                )
                ORDER BY created_at ASC, rowid ASC
                """,
                (session_id, self.max_messages),
            )
            return [ChatMessage(role=row[0], content=row[1]) for row in cursor.fetchall()]

    def append_turn(self, session_id: str, user_question: str, assistant_answer: str) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.executemany(
                """
                INSERT INTO agent_session_messages (session_id, role, content)
                VALUES (?, ?, ?)
                """,
                [
                    (session_id, "user", user_question),
                    (session_id, "assistant", assistant_answer),
                ],
            )
            connection.execute(
                """
                DELETE FROM agent_session_messages
                WHERE rowid IN (
                    SELECT rowid
                    FROM agent_session_messages
                    WHERE session_id = ?
                    ORDER BY created_at DESC, rowid DESC
                    LIMIT -1 OFFSET ?
                )
                """,
                (session_id, self.max_messages),
            )
            connection.commit()

    def load_summary(self, session_id: str) -> str | None:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                SELECT summary
                FROM agent_session_summaries
                WHERE session_id = ?
                """,
                (session_id,),
            )
            row = cursor.fetchone()
            return str(row[0]) if row and row[0] else None

    def store_summary(self, session_id: str, summary: str | None) -> None:
        if not summary:
            return
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO agent_session_summaries (session_id, summary, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(session_id) DO UPDATE SET
                    summary = excluded.summary,
                    updated_at = excluded.updated_at
                """,
                (session_id, summary),
            )
            connection.commit()

    def load_facts(self, session_id: str) -> dict[str, str]:
        with sqlite3.connect(self.database_path) as connection:
            cursor = connection.execute(
                """
                SELECT fact_key, fact_value
                FROM agent_session_facts
                WHERE session_id = ?
                ORDER BY fact_key ASC
                """,
                (session_id,),
            )
            return {str(row[0]): str(row[1]) for row in cursor.fetchall()}

    def store_facts(self, session_id: str, facts: dict[str, str]) -> None:
        if not facts:
            return
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                "DELETE FROM agent_session_facts WHERE session_id = ?",
                (session_id,),
            )
            connection.executemany(
                """
                INSERT INTO agent_session_facts (session_id, fact_key, fact_value)
                VALUES (?, ?, ?)
                """,
                [(session_id, key, value) for key, value in facts.items()],
            )
            connection.commit()

    def append_trace(
        self,
        request_id: str,
        session_id: str | None,
        runtime_mode: str,
        route: str,
        tool_name: str,
        grounded: bool,
        note: str,
    ) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO agent_run_traces (
                    request_id, session_id, runtime_mode, route, tool_name, grounded, note
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (request_id, session_id, runtime_mode, route, tool_name, int(grounded), note),
            )
            connection.commit()

    def _initialize(self) -> None:
        with sqlite3.connect(self.database_path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_session_messages (
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_session_summaries (
                    session_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_session_facts (
                    session_id TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    PRIMARY KEY (session_id, fact_key)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_run_traces (
                    request_id TEXT NOT NULL,
                    session_id TEXT,
                    runtime_mode TEXT NOT NULL,
                    route TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    grounded INTEGER NOT NULL,
                    note TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.commit()
