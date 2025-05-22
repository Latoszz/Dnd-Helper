from langchain.tools.retriever import create_retriever_tool
from langchain.tools.tavily_search import TavilySearchResults
from langchain_core.retrievers import BaseRetriever


class ToolFactory:
    def __init__(self, retriever: BaseRetriever):
        self.retriever = retriever

    def create_vector_retriever_tool(self):
        return create_retriever_tool(
            retriever=self.retriever,
            name="retrieve_dnd",
            description="Search and return information from the D&D 5e Player's Handbook."
        )

    def create_tavily_tool(self):
        return TavilySearchResults(max_results=5)

    def create_tools(self):
        return [self.create_vector_retriever_tool(), self.create_tavily_tool()]