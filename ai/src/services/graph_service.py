from managers.config_manager import Config
from factories.tool_factory import ToolFactory
from factories.agent_factory import AgentFactory
from services.workflow_service import WorkflowService
from langchain_openai import ChatOpenAI
from langchain_core.retrievers import BaseRetriever


def build_graph(retriever: BaseRetriever):
    config_obj = Config()

    llm = ChatOpenAI(
        openai_api_key=config_obj.key,
        model=config_obj.model,
        temperature=config_obj.temperature,
    )

    tool_factory = ToolFactory(retriever)
    tools = tool_factory.create_tools()
    agent_factory = AgentFactory(llm, tools)

    agents = {
        "search": agent_factory.create_agent("search"),
        "writer": agent_factory.create_agent("writer"),
    }

    workflow = WorkflowService(agents, tools).build()

    graph = workflow.compile()

    return graph