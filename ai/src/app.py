from ai.src.agents.agent_factory import AgentFactory
from ai.src.managers.config_manager import Config
from ai.src.services.workflow_service import WorkflowService
from backend.src.app import create_vector_store

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool


def main():
    config_obj = Config()

    llm = ChatOpenAI(
        openai_api_key=config_obj.key,
        model=config_obj.model,
        temperature=config_obj.temperature
    )

    question = input('Your question: ')

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

    workflow = WorkflowService(agents, tools).build()

    graph = workflow.compile()

    input_message = HumanMessage(content=question)

    for event in graph.stream({"messages": [input_message]}, stream_mode="values"):
        event['messages'][-1].pretty_print()

if __name__ == "__main__":
    main()
