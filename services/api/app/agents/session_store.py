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
            connection.commit()
