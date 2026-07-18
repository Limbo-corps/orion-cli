from __future__ import annotations

from typing import cast

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

from memory.planner.planner_models import RetrievalPlan
from memory.planner.planner_prompt import SYSTEM_PROMPT


class RetrievalPlanner:
    def __init__(
        self,
        llm: BaseChatModel,
    ) -> None:
        self.chain = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{query}"),
            ]
        ) | llm.with_structured_output(RetrievalPlan)

    async def plan(
        self,
        query: str,
    ) -> RetrievalPlan:
        result = await self.chain.ainvoke(
            {
                "query": query,
            }
        )

        return cast(RetrievalPlan, result)
