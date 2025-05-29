import asyncio
from typing import cast
from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager

from langchain.chains.question_answering.map_reduce_prompt import messages
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_core.runnables import RunnableConfig
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage
from managers.config_manager import Config
from services.vector_store_service import create_vector_store
from services.graph_service import build_graph
from models.query import Query


def get_retriever() -> VectorStoreRetriever:
    return cast(VectorStoreRetriever, app.state.retriever)


def get_langgraph() -> CompiledStateGraph:
    return cast(CompiledStateGraph, app.state.graph)


config = Config()

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    app.state.retriever = create_vector_store(config=config).as_retriever()
    app.state.graph = build_graph(get_retriever())
    logger.info(get_langgraph().get_graph().draw_mermaid())
    yield
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)


@app.post("/embed")
async def embed():
    app.state.retriver = create_vector_store(
        recreate=True, config=config
    ).as_retriever()
    return {"message": "Vector Store has been updated"}


@app.post("/generate")
async def generate(query: Query):
    graph = get_langgraph()
    input_message = HumanMessage(content=query.question)

    # runnable_config = RunnableConfig(
    #     configurable={
    #         "provider": query.provider,
    #         "model": query.model,
    #         "temperature": query.temperature,
    #     }
    # )
    logger.info(input_message)

    return graph.invoke({"messages": [input_message]})
    # return graph.with_config(
    #     configurable={
    #         "provider": query.provider,
    #         "model": query.model,
    #         "temperature": query.temperature,
    #     }
    # ).invoke({"messages": [input_message]})


if __name__ == "__main__":
    query=Query(question="What is your name?", provider="google_genai", model="gemini-flash-2.0", temperature=0.5)
    print(asyncio.run(generate(query)))