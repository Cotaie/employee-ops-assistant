from typing import Annotated, Any

from langchain_core.tools import BaseTool, tool
from pydantic import Field

from agent_api.app.clients.retrieve import RetrieveApiClient


def create_retrieval_tools(client: RetrieveApiClient) -> list[BaseTool]:
    """Create the internal knowledge-retrieval tool exposed to the agent."""

    @tool
    async def retrieve_knowledge(
        query: str,
        top_k: Annotated[int, Field(ge=1, le=20)] = 5,
    ) -> dict[str, Any]:
        """Retrieve semantically relevant chunks from indexed internal documents."""

        return await client.retrieve(query, top_k)

    return [retrieve_knowledge]
