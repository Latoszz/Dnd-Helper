from ai.src.agents.agent_state import AgentState
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage
import functools
from typing import Literal


class WorkflowService:
    def __init__(self, agent_factory, tools):
        self.agent_factory = agent_factory
        self.tools = tools
        self.workflow = StateGraph(AgentState)

    def _setup_nodes(self):
        self.workflow.add_node("search", self.agent_factory.create_agent_node("search"))
        self.workflow.add_node("writer", self.agent_factory.create_agent_node("writer"))
        self.workflow.add_node("tools", ToolNode(self.tools))


    def _setup_edges(self):
        self.workflow.set_entry_point("search")

        # Search node transitions
        self.workflow.add_conditional_edges(
            "search",
            self._should_search,
        )

        # Tools node always returns to search
        self.workflow.add_edge("tools", "search")

        self.workflow.set_finish_point("writer")

    def _should_search(self, state) -> Literal["tools", "writer"]:
        messages = state["messages"]
        last_message = messages[-1]
        # If the LLM makes a tool call, then we route to the "tools" node
        if last_message.tool_calls:
            return "tools"
        # Otherwise, we stop (reply to the user)
        return "writer"

    def build(self):
        self._setup_nodes()
        self._setup_edges()
        return self.workflow
