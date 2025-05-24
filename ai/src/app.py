from typing import cast
from fastapi import FastAPI, HTTPException
import logging
from contextlib import asynccontextmanager
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage
from managers.config_manager import Config
from services.vector_store_service import VectorStoreService
from services.graph_service import build_graph
from models.query import Query


def get_vector_store_service() -> VectorStoreService:
    return cast(VectorStoreService, app.state.vector_store_service)


def get_langgraph() -> CompiledStateGraph:
    return cast(CompiledStateGraph, app.state.graph)


config = Config()
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up")
    app.state.vector_store_service = VectorStoreService(config=config)
    app.state.graph = build_graph(get_vector_store_service().as_retriever())
    logger.info(get_langgraph().get_graph().draw_mermaid())
    yield
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)


@app.post("/embed")
async def embed():
    try:
        return {
            "message": "Vector Store has been updated",
            "details": get_vector_store_service().add_to_vector_store(),
        }
    except Exception as err:
        logger.error(err)
        raise HTTPException(
            status_code=500,
            detail="Internal issues, database hasn't been updated. Try later :0",
        )


@app.post("/generate")
async def generate(query: Query):
    graph = get_langgraph()
    input_message = HumanMessage(content=query.question)
    logger.info(input_message)
    try:
        return graph.invoke({"messages": [input_message]}, stream_mode="values")
    except Exception as err:
        logger.error(err)
        raise HTTPException(
            status_code=500, detail="You dont have enough of tokens or you messed up :0"
        )
