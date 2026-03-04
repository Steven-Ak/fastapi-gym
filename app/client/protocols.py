from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMClientProtocol(Protocol):
    async def generate_workout_plan(self, profile: dict) -> dict: ...
