from agents.agent_factory import AgentFactory
from managers.config_manager import Config
from services.workflow_service import WorkflowService
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools.retriever import create_retriever_tool
from langchain_core.retrievers import BaseRetriever


def build_graph(retriever: BaseRetriever):
    config_obj = Config()

    llm = ChatOpenAI(
        openai_api_key=config_obj.key,
        model=config_obj.model,
        temperature=config_obj.temperature,
        use_responses_api=True,
    )

    retriever_tool = create_retriever_tool(
        retriever=retriever,
        name="retrieve_dnd",
        description="Search and return information about dungeons and dragons",
    )
    tools = [retriever_tool, TavilySearchResults(max_results=5)]
    agent_factory = AgentFactory(llm, tools)

    agents = {
        "search": agent_factory.create_agent("search"),
        "writer": agent_factory.create_agent("writer"),
    }

    workflow = WorkflowService(agents, tools).build()

    graph = workflow.compile()

    return graph


if __name__ == "__main__":
    build_graph()
