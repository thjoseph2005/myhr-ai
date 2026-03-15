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


def test_session_store_persists_summary_facts_and_trace(tmp_path) -> None:
    store = AgentSessionStore(str(tmp_path / "agent-memory.sqlite3"), max_messages=4)

    store.store_summary("session-1", "User asked about PTO.")
    store.store_facts("session-1", {"employee": "Priya Nair"})
    store.append_trace(
        request_id="req-1",
        session_id="session-1",
        runtime_mode="manual",
        route="structured_hr",
        tool_name="hr_sql_tool",
        grounded=True,
        note="test trace",
    )

    assert store.load_summary("session-1") == "User asked about PTO."
    assert store.load_facts("session-1") == {"employee": "Priya Nair"}
