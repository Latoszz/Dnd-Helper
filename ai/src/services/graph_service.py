from langchain_core.messages import HumanMessage

from ai.src.managers.config_manager import Config
from ai.src.factories.tool_factory import ToolFactory
from ai.src.factories.agent_factory import AgentFactory
from ai.src.factories.llm_factory import LLMFactory
from ai.src.services.vector_store_service import create_vector_store
from ai.src.services.workflow_service import WorkflowService
from langchain_core.retrievers import BaseRetriever

config_obj = Config()
retriever = create_vector_store(config=config_obj).as_retriever()

def build_graph(retriever: BaseRetriever):

    llm_factory = LLMFactory(config_obj)

    tool_factory = ToolFactory(retriever)
    tools = tool_factory.create_tools()

    agent_factory = AgentFactory(llm_factory, tools)

    workflow = WorkflowService(agent_factory, tools).build()

    graph = workflow.compile()

    return graph


if __name__ == "__main__":
    graph = build_graph(retriever)

    query = {
        "messages": HumanMessage(content="How to start"),
        "model": "gpt-4o-mini",
        "temperature": 0.5,
    }

    graph.invoke(query)
