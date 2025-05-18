from ai.src.agents.agent_factory import AgentFactory
from ai.src.managers.config_manager import Config
from backend.src.app import create_vector_store

from typing_extensions import TypedDict
from typing import Literal, Annotated
import functools

from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool

from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
  messages: Annotated[list, add_messages]


def main():
    config_obj = Config()

    llm = ChatOpenAI(
        openai_api_key=config_obj.key,
        model=config_obj.model,
        temperature=config_obj.temperature
    )

    question = "How to make the most powerful fireball"

    retriever = create_vector_store().as_retriever()
    retriever_tool = create_retriever_tool(
        retriever,
        "retrieve_dnd",
        "Search and return information about dungeons and dragons",
    )
    tools = [retriever_tool, TavilySearchResults(max_results=5)]
    agent_factory = AgentFactory(llm, tools)

    agents = {
        "search": agent_factory.create_agent("search"),
        "writer": agent_factory.create_agent("writer"),
    }

    search_agent = agents['search']
    writer_agent = agents['writer']

    search_node = functools.partial(agent_node, agent=search_agent, name="Search Agent")
    writer_node = functools.partial(agent_node, agent=writer_agent, name="Writer Agent")
    tool_node = ToolNode(tools)

    workflow = StateGraph(AgentState)

    # Nodes
    workflow.add_node("search", search_node)
    workflow.add_node("tools", tool_node)
    workflow.add_node("writer", writer_node)

    # Edges
    workflow.set_entry_point("search")
    workflow.add_conditional_edges(
        "search",
        should_search,
    )
    workflow.add_edge("tools", 'search')
    workflow.set_finish_point("writer")

    graph = workflow.compile()

    input_message = HumanMessage(content=question)

    for event in graph.stream({"messages": [input_message]}, stream_mode="values"):
        event['messages'][-1].pretty_print()

def agent_node(state, agent, name):
  result = agent.invoke(state)
  return {
      'messages': [result]
  }

def should_search(state) -> Literal["tools", "writer"]:
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return "writer"

if __name__ == "__main__":
    main()
