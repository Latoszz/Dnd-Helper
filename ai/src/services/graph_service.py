from managers.config_manager import Config
from factories.tool_factory import ToolFactory
from services.workflow_service import WorkflowService
from langchain_core.retrievers import BaseRetriever


def build_graph(retriever: BaseRetriever):
    config_obj = Config()
    tool_factory = ToolFactory(retriever)
    tools = tool_factory.create_tools()

    workflow = WorkflowService(tools, config_obj).build()

    graph = workflow.compile()

    return graph
