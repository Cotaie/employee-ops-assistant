from uuid import uuid4

from contracts import ThreadResponse
from fastapi import APIRouter, status

from agent_api.app.dependencies.auth import CurrentUserDependency

router = APIRouter(prefix="/threads", tags=["threads"])


@router.post(
    "",
    response_model=ThreadResponse,
    status_code=status.HTTP_201_CREATED,
    name="create_thread",
    summary="Create a conversation thread",
)
async def create_thread(current_user: CurrentUserDependency) -> ThreadResponse:
    return ThreadResponse(thread_id=uuid4())
