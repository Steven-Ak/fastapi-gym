from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    async def generate_workout_plan(self, profile: dict) -> dict: ...
    async def answer_exercise_question(
        self, question: str, context: str,
        injuries: str | None = None, diseases: str | None = None,
    ) -> str: ...


@runtime_checkable
class EmbeddingClientProtocol(Protocol):
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    async def embed_query(self, text: str) -> list[float]: ...
