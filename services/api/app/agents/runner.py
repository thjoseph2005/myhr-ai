from __future__ import annotations

from dataclasses import replace
from uuid import uuid4

from openai import AsyncOpenAI

from app.agents.context import AgentContext
from app.agents.memory_manager import AgentMemoryManager
from app.agents.models import AgentExecutionResult
from app.agents.session_store import AgentSessionStore
from app.agents.supervisor_agent import SUPERVISOR_INSTRUCTIONS, SupervisorAgent
from app.core.logging import get_logger
from app.schemas.agent_runtime import SupervisorAgentOutput
from app.schemas.chat import ChatMessage, ChatRequest, ChatResponse

try:
    from agents import Agent as OpenAIAgent
    from agents import Runner as OpenAIRunner
    from agents import SQLiteSession as OpenAISQLiteSession
    from agents import function_tool as openai_function_tool
    from agents import set_default_openai_api
    from agents import set_default_openai_client
    from agents import set_tracing_disabled
except ImportError:  # pragma: no cover - optional dependency at runtime
    OpenAIAgent = None
    OpenAIRunner = None
    OpenAISQLiteSession = None
    openai_function_tool = None
    set_default_openai_api = None
    set_default_openai_client = None
    set_tracing_disabled = None

logger = get_logger(__name__)


class AgentRunnerService:
    sdk_agent_class = OpenAIAgent
    sdk_runner = OpenAIRunner
    sdk_function_tool = openai_function_tool
    sdk_session_class = OpenAISQLiteSession
    sdk_set_client = set_default_openai_client
    sdk_set_api = set_default_openai_api
    sdk_disable_tracing = set_tracing_disabled
    sdk_async_client_class = AsyncOpenAI

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.session_store = AgentSessionStore(
            context.settings.agent_memory_path,
            max_messages=context.settings.max_history_messages,
        )
        self.memory_manager = AgentMemoryManager(context.answer_generation_service)

    async def run_chat(self, payload: ChatRequest) -> ChatResponse:
        session_id = payload.session_id
        memory_summary = self.session_store.load_summary(session_id) if session_id else None
        remembered_facts = self.session_store.load_facts(session_id) if session_id else {}
        history = self._resolve_history(payload, memory_summary, remembered_facts)
        runtime_context = replace(
            self.context,
            request_id=str(uuid4()),
            session_id=session_id,
            memory_summary=memory_summary,
            remembered_facts=remembered_facts,
        )
        route = runtime_context.llm_router_service.route(payload.question, history)
        result = await self._run_agent(payload.question, history, runtime_context)
        if session_id:
            self.session_store.append_turn(session_id, payload.question, result.answer)
            recent_history = self.session_store.load_history(session_id)
            summary, facts = self.memory_manager.update_memory(
                memory_summary,
                remembered_facts,
                recent_history,
            )
            self.session_store.store_summary(session_id, summary)
            self.session_store.store_facts(session_id, facts)
        self.session_store.append_trace(
            request_id=runtime_context.request_id,
            session_id=session_id,
            runtime_mode="sdk" if runtime_context.settings.openai_agents_enabled else "manual",
            route=route.route,
            tool_name=result.tool_name,
            grounded=result.grounded,
            note=route.reason,
        )
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
                logger.info(
                    "agent_runtime_selected mode=%s tool=%s request_id=%s session_id=%s",
                    "sdk",
                    sdk_result.tool_name,
                    runtime_context.request_id,
                    runtime_context.session_id or "",
                )
                return sdk_result

        supervisor = SupervisorAgent(runtime_context)
        fallback_result = supervisor.run(question, history)
        logger.info(
            "agent_runtime_selected mode=%s tool=%s request_id=%s session_id=%s",
            "manual",
            fallback_result.tool_name,
            runtime_context.request_id,
            runtime_context.session_id or "",
        )
        return fallback_result

    async def _run_with_agents_sdk(
        self,
        question: str,
        history: list[ChatMessage],
        runtime_context: AgentContext,
    ) -> AgentExecutionResult | None:
        if not runtime_context.settings.azure_enabled:
            return None
        if self.sdk_agent_class is None or self.sdk_runner is None or self.sdk_function_tool is None:
            return None
        if self.sdk_set_client is None or self.sdk_set_api is None or self.sdk_disable_tracing is None:
            return None

        try:
            self._configure_sdk(runtime_context)

            @self.sdk_function_tool
            def search_policy_tool(tool_question: str) -> dict[str, object]:
                result = runtime_context.policy_search_tool.run(tool_question, history)
                return {
                    "selected_tool": "policy_search_tool",
                    "answer": result.answer,
                    "grounded": result.grounded,
                    "citations": [citation.model_dump() for citation in result.citations],
                    "rationale": "Policy retrieval result.",
                }

            @self.sdk_function_tool
            def query_hr_database_tool(tool_question: str) -> dict[str, object]:
                result = runtime_context.hr_sql_tool.run(tool_question)
                return {
                    "selected_tool": "hr_sql_tool",
                    "answer": result.answer,
                    "grounded": result.grounded,
                    "citations": [citation.model_dump() for citation in result.citations],
                    "rationale": "Structured HR database result.",
                }

            @self.sdk_function_tool
            def hybrid_answer_tool(tool_question: str) -> dict[str, object]:
                result = runtime_context.hybrid_answer_tool.run(tool_question, history)
                return {
                    "selected_tool": "hybrid_answer_tool",
                    "answer": result.answer,
                    "grounded": result.grounded,
                    "citations": [citation.model_dump() for citation in result.citations],
                    "rationale": "Hybrid policy and structured HR result.",
                }

            supervisor = self.sdk_agent_class(  # type: ignore[call-arg]
                name="myhr-ai-supervisor",
                instructions=SUPERVISOR_INSTRUCTIONS,
                model=runtime_context.settings.azure_openai_chat_deployment,
                tools=[search_policy_tool, query_hr_database_tool, hybrid_answer_tool],
                output_type=SupervisorAgentOutput,
            )
            runner_kwargs: dict[str, object] = {}
            if runtime_context.session_id and self.sdk_session_class is not None:
                runner_kwargs["session"] = self.sdk_session_class(
                    runtime_context.session_id,
                    runtime_context.settings.agent_memory_path,
                )

            result = await self.sdk_runner.run(  # type: ignore[attr-defined]
                supervisor,
                input=question,
                **runner_kwargs,
            )
            final_output = getattr(result, "final_output", None)
            parsed = self._parse_sdk_output(final_output)
            if parsed is None:
                return None
            return AgentExecutionResult(
                answer=parsed.answer,
                citations=parsed.citations,
                grounded=parsed.grounded,
                tool_name=parsed.selected_tool,
            )
        except Exception as exc:
            logger.warning(
                "agent_sdk_fallback reason=%s request_id=%s session_id=%s",
                str(exc),
                runtime_context.request_id,
                runtime_context.session_id or "",
            )
            return None

    def _configure_sdk(self, runtime_context: AgentContext) -> None:
        client = self.sdk_async_client_class(
            api_key=runtime_context.settings.azure_openai_api_key,
            base_url=f"{runtime_context.settings.azure_openai_endpoint.rstrip('/')}/openai/v1/",
        )
        self.sdk_set_client(client, use_for_tracing=False)
        self.sdk_set_api("chat_completions")
        self.sdk_disable_tracing(True)

    @staticmethod
    def _parse_sdk_output(final_output: object) -> SupervisorAgentOutput | None:
        if isinstance(final_output, SupervisorAgentOutput):
            return final_output
        if isinstance(final_output, dict):
            try:
                return SupervisorAgentOutput.model_validate(final_output)
            except Exception:
                return None
        return None

    def _resolve_history(
        self,
        payload: ChatRequest,
        memory_summary: str | None,
        remembered_facts: dict[str, str],
    ) -> list[ChatMessage]:
        memory_messages: list[ChatMessage] = []
        if memory_summary:
            facts_block = ""
            if remembered_facts:
                facts_block = "\n".join(f"- {key}: {value}" for key, value in remembered_facts.items())
            content = f"Conversation memory summary: {memory_summary}"
            if facts_block:
                content += f"\nRemembered facts:\n{facts_block}"
            memory_messages.append(ChatMessage(role="assistant", content=content))
        if payload.session_id:
            stored_history = self.session_store.load_history(payload.session_id)
            if stored_history and not payload.history:
                merged = [*memory_messages, *stored_history]
                return merged[-self.context.settings.max_history_messages :]
            if stored_history:
                merged = [*memory_messages, *stored_history, *payload.history]
                return merged[-self.context.settings.max_history_messages :]

        merged = [*memory_messages, *payload.history]
        return merged[-self.context.settings.max_history_messages :]
