from uuid import UUID

from pydantic import BaseModel


class ThreadResponse(BaseModel):
    thread_id: UUID
