from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message_id: UUID = Field(
        description="Stable client-generated identifier used to make message retries idempotent.",
    )
    message: str = Field(
        min_length=1,
        max_length=10_000,
        description="The user's message to the agent.",
    )
