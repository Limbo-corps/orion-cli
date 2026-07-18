from pydantic import BaseModel, Field


class RetrievalPlan(BaseModel):
    retrieve_summary: bool = False
    retrieve_facts: bool = False
    retrieve_conversations: bool = False

    search_queries: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)

    top_k: int = 5
