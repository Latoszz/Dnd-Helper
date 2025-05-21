from typing import cast
from fastapi import FastAPI
from pydantic import BaseModel
from contextlib import asynccontextmanager
from langchain.vectorstores.base import VectorStoreRetriever
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage
from managers.config_manager import Config
from services.vector_store_service import create_vector_store
from services.graph_service import build_graph
import logging


class Query(BaseModel):
    question: str


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
    return {"result": graph.invoke(input_message)}
