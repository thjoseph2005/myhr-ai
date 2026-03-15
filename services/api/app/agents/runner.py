from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from app.agents.context import AgentContext
from app.agents.models import AgentExecutionResult
from app.agents.session_store import AgentSessionStore
from app.agents.supervisor_agent import SupervisorAgent
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

try:
    from agents import Agent as OpenAIAgent
    from agents import Runner as OpenAIRunner
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAIAgent = None
    OpenAIRunner = None


class AgentRunnerService:
    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.session_store = AgentSessionStore(
            context.settings.agent_memory_path,
            max_messages=context.settings.max_history_messages,
        )

    async def run_chat(self, payload: ChatRequest) -> ChatResponse:
        history = self._resolve_history(payload)
        session_id = payload.session_id
        runtime_context = replace(
            self.context,
            request_id=str(uuid4()),
            session_id=session_id,
        )
        result = await self._run_agent(payload.question, history, runtime_context)
        if session_id:
            self.session_store.append_turn(session_id, payload.question, result.answer)
        return ChatResponse(
            answer=result.answer,
            citations=result.citations,
            grounded=result.grounded,
        )

    async def _run_agent(
        self,
        question: str,
        history: list[ChatMessage],
        runtime_context: AgentContext,
    ) -> AgentExecutionResult:
        if runtime_context.settings.openai_agents_enabled:
            sdk_result = await self._run_with_agents_sdk(question, history, runtime_context)
            if sdk_result is not None:
                return sdk_result

        supervisor = SupervisorAgent(runtime_context)
        return supervisor.run(question, history)

    async def _run_with_agents_sdk(
        self,
        question: str,
        history: list[ChatMessage],
        runtime_context: AgentContext,
    ) -> AgentExecutionResult | None:
        if OpenAIAgent is None or OpenAIRunner is None:
            return None

        try:
            policy_result = runtime_context.policy_search_tool.run(question, history)
            sql_result = runtime_context.hr_sql_tool.run(question)
            supervisor = OpenAIAgent(  # type: ignore[call-arg]
                name="myhr-ai-supervisor",
                instructions=(
                    "Choose the best answer from the provided tool results. "
                    "Prefer the SQL result for structured HR questions and the policy result for policy questions. "
                    "If neither result is grounded, return the exact fallback message."
                ),
                model=runtime_context.settings.azure_openai_chat_deployment,
            )
            tool_summary = {
                "policy_result": {
                    "answer": policy_result.answer,
                    "grounded": policy_result.grounded,
                    "citations": [citation.model_dump() for citation in policy_result.citations],
                },
                "sql_result": {
                    "answer": sql_result.answer,
                    "grounded": sql_result.grounded,
                    "citations": [citation.model_dump() for citation in sql_result.citations],
                },
            }
            result = await OpenAIRunner.run(supervisor, input=[  # type: ignore[attr-defined]
                {
                    "role": "user",
                    "content": (
                        f"Question: {question}\n"
                        f"Conversation history size: {len(history)}\n"
                        f"Tool results: {tool_summary}"
                    ),
                }
            ])
            final_output = getattr(result, "final_output", None)
            if isinstance(final_output, str) and sql_result.grounded and "policy" not in final_output.lower():
                return AgentExecutionResult(
                    answer=sql_result.answer,
                    citations=sql_result.citations,
                    grounded=sql_result.grounded,
                    tool_name="hr_sql_tool",
                )
            if isinstance(final_output, str) and policy_result.grounded:
                return AgentExecutionResult(
                    answer=policy_result.answer,
                    citations=policy_result.citations,
                    grounded=policy_result.grounded,
                    tool_name="policy_search_tool",
                )
        except Exception:
            return None

        return None

    def _resolve_history(self, payload: ChatRequest) -> list[ChatMessage]:
        if payload.session_id:
            stored_history = self.session_store.load_history(payload.session_id)
            if stored_history and not payload.history:
                return stored_history[-self.context.settings.max_history_messages :]
            if stored_history:
                merged = [*stored_history, *payload.history]
                return merged[-self.context.settings.max_history_messages :]

        return payload.history[-self.context.settings.max_history_messages :]
