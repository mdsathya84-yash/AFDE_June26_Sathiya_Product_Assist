import logging
from typing import Optional
import openai
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from backend.core.config import settings

logger = logging.getLogger(__name__)


class LLMUnavailableError(Exception):
    pass


class LLMRouter:
    """
    Routes LLM calls: OpenAI gpt-4o-mini → gpt-3.5-turbo → Groq llama-3.3-70b.
    Failover triggers on rate limits and server errors, NOT on auth/bad-request errors.
    SSL verification is disabled at process level in main.py when OPENAI_BASE_URL is set.
    """

    def __init__(self):
        # langchain-openai 1.x uses openai_api_base (not base_url) to set a custom endpoint.
        openai_kwargs: dict = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            openai_kwargs["openai_api_base"] = settings.OPENAI_BASE_URL

        self.openai_llm = ChatOpenAI(
            **openai_kwargs,
            model=settings.OPENAI_MODEL,
            temperature=0.1,
            max_tokens=4096,
            timeout=60,
        )
        self.openai_fast_llm = ChatOpenAI(
            **openai_kwargs,
            model=settings.OPENAI_FALLBACK_MODEL,
            temperature=0.1,
            max_tokens=4096,
            timeout=60,
        )
        groq_key = settings.GROQ_API_KEY
        self.groq_llm = (
            ChatGroq(
                api_key=groq_key,
                model=settings.GROQ_MODEL,
                temperature=0.1,
                max_tokens=2048,
                timeout=30,
            )
            if groq_key
            else None
        )
        self._active_provider = "openai-gpt4o-mini"
        self._fallback_count = 0

    def _build_messages(self, messages: list) -> list:
        result = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                result.append(SystemMessage(content=content))
            else:
                result.append(HumanMessage(content=content))
        return result

    def _is_fatal_error(self, exc: Exception) -> bool:
        """Auth and bad-request errors should not trigger fallback."""
        if isinstance(exc, openai.AuthenticationError):
            return True
        if isinstance(exc, openai.BadRequestError):
            return True
        return False

    async def invoke(self, messages: list, json_mode: bool = False) -> str:
        lc_messages = self._build_messages(messages)
        # json_mode is handled via system-prompt instructions in each agent.
        # We do NOT send response_format={"type":"json_object"} because many
        # OpenAI-compatible gateways reject the object form (expecting a string).

        # Step 1: OpenAI gpt-4o-mini
        try:
            response = await self.openai_llm.ainvoke(lc_messages)
            self._active_provider = "openai-gpt4o-mini"
            return response.content
        except Exception as e:
            if self._is_fatal_error(e):
                raise
            logger.warning("gpt-4o-mini failed (%s), trying gpt-3.5-turbo", e)

        # Step 2: OpenAI gpt-3.5-turbo
        try:
            response = await self.openai_fast_llm.ainvoke(lc_messages)
            self._active_provider = "openai-gpt35"
            self._fallback_count += 1
            logger.warning("Using fallback: openai-gpt35")
            return response.content
        except Exception as e:
            if self._is_fatal_error(e):
                raise
            logger.warning("gpt-3.5-turbo failed (%s), trying Groq", e)

        # Step 3: Groq llama-3.3-70b
        if self.groq_llm is None:
            raise LLMUnavailableError("All OpenAI tiers failed and Groq is not configured")
        try:
            response = await self.groq_llm.ainvoke(lc_messages)
            self._active_provider = "groq-70b"
            self._fallback_count += 1
            logger.warning("Using fallback: groq-70b")
            return response.content
        except Exception as e:
            raise LLMUnavailableError(f"All LLM providers failed: {e}") from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APIConnectionError)),
        reraise=True,
    )
    async def invoke_with_retry(self, messages: list, json_mode: bool = False) -> str:
        return await self.invoke(messages, json_mode=json_mode)

    def get_active_provider(self) -> str:
        return self._active_provider

    def get_health(self) -> dict:
        return {
            "primary": "openai",
            "primary_model": settings.OPENAI_MODEL,
            "primary_fallback_model": settings.OPENAI_FALLBACK_MODEL,
            "openai_base_url": settings.OPENAI_BASE_URL or "default (api.openai.com)",
            "secondary": "groq" if self.groq_llm else "not_configured",
            "secondary_model": settings.GROQ_MODEL,
            "active_provider": self._active_provider,
            "fallback_count": self._fallback_count,
        }


_router: Optional[LLMRouter] = None


def get_llm_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter()
    return _router
