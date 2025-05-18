from ai.src.agents.agent_factory import AgentFactory
from ai.src.managers.config_manager import Config

from typing_extensions import TypedDict
from typing import Literal, Annotated
import functools

from langchain_openai import ChatOpenAI
from langchain_core.messages import AnyMessage, HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults

from langgraph.graph import StateGraph, END
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

    tools = [TavilySearchResults(max_results=5)]
    agent_factory = AgentFactory(llm, tools)

    agents = {
        "search": agent_factory.create_agent("search"),
        "outliner": agent_factory.create_agent("outliner"),
        "writer": agent_factory.create_agent("writer"),
        "editor": agent_factory.create_agent("editor")
    }
    return llm, tools, agents

def agent_node(state, agent, name):
  result = agent.invoke(state)
  return {
      'messages': [result]
  }

def editor_node(state):
  result = editor_agent.invoke(state)
  N = state["no_of_iterations"] + 1
  return {
      "messages": [result],
      "no_of_iterations": N
  }

def should_search(state) -> Literal["tools", "outliner"]:
    messages = state['messages']
    last_message = messages[-1]
    # If the LLM makes a tool call, then we route to the "tools" node
    if last_message.tool_calls:
        return "tools"
    # Otherwise, we stop (reply to the user)
    return "outliner"

llm, tools, agents = main()

search_agent = agents['search']
outliner_agent = agents['outliner']
writer_agent = agents['writer']
editor_agent = agents['editor']

search_node = functools.partial(agent_node, agent=search_agent, name="Search Agent")
outliner_node = functools.partial(agent_node, agent=outliner_agent, name="Outliner Agent")
writer_node = functools.partial(agent_node, agent=writer_agent, name="Writer Agent")
tool_node = ToolNode(tools)

workflow = StateGraph(AgentState)

#Nodes
workflow.add_node("search", search_node)
workflow.add_node("tools", tool_node)
workflow.add_node("outliner", outliner_node)
workflow.add_node("writer", writer_node)

#Edges
workflow.set_entry_point("search")
workflow.add_conditional_edges(
    "search",
    should_search,
)
workflow.add_edge("tools", 'search')
workflow.add_edge("outliner", "writer")
workflow.add_edge("writer", END)

graph = workflow.compile()

question = "Write a review about movie cars 2"
input_message = HumanMessage(content=question)


for event in graph.stream({"messages": [input_message]}, stream_mode="values"):
  event['messages'][-1].pretty_print()
