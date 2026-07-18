from pydantic import BaseModel, Field


class ApprovalRequest(BaseModel):
    interrupt_id: str = Field(min_length=1)
    approved: bool
