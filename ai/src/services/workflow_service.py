from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph
from langchain_core.messages import AIMessage
import functools
from typing import Literal
from langgraph.prebuilt.chat_agent_executor import AgentState


class WorkflowService:
    def __init__(self, agents, tools):
        self.agents = agents
        self.tools = tools
        self.workflow = StateGraph(AgentState)

    def _create_agent_node(self, state, agent, name):
        result = agent.invoke(state)

        if isinstance(result, AIMessage):
            result.name = name
            return {"messages": [result]}

        return {"messages": [AIMessage(content=result.content, tool_calls=result.tool_calls, name=name)]}

    def _setup_nodes(self):
        nodes = {
            "search": functools.partial(
                self._create_agent_node,
                agent=self.agents["search"],
                name="Search_Agent",
            ),
            "writer": functools.partial(
                self._create_agent_node,
                agent=self.agents["writer"],
                name="Writer_Agent",
            ),
            "tools": ToolNode(self.tools),
        }

        for name, node in nodes.items():
            self.workflow.add_node(name, node)

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
