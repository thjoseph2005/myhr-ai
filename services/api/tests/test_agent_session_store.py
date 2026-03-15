from app.agents.session_store import AgentSessionStore


def test_session_store_returns_latest_messages_in_order(tmp_path) -> None:
    store = AgentSessionStore(str(tmp_path / "agent-memory.sqlite3"), max_messages=4)

    store.append_turn("session-1", "Question one", "Answer one")
    store.append_turn("session-1", "Question two", "Answer two")
    store.append_turn("session-1", "Question three", "Answer three")

    history = store.load_history("session-1")

    assert [message.content for message in history] == [
        "Question two",
        "Answer two",
        "Question three",
        "Answer three",
    ]
