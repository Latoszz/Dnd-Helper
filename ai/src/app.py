import logging
import asyncio
from typing import cast
from fastapi import FastAPI, HTTPException
from fastapi import UploadFile
from contextlib import asynccontextmanager
from langchain.chains.question_answering.map_reduce_prompt import messages
from langchain.vectorstores.base import VectorStoreRetriever
from langchain_core.runnables import RunnableConfig
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
    app.state.vector_store_service = await VectorStoreService.create(
        config=config, to_reembed=False
    )
    app.state.graph = build_graph(get_vector_store_service().as_retriever())
    logger.info(get_langgraph().get_graph().draw_mermaid())
    yield
    logger.info("Shutting down")


app = FastAPI(lifespan=lifespan)


@app.post("/embed")
async def embed(file: UploadFile):
    try:
        vector_store = get_vector_store_service()
        match file.content_type:
            case "text/plain":
                file_type = ".txt"
            case "application/pdf":
                file_type = ".pdf"
            case _:
                logger.error("Not allowed file type")
                raise HTTPException(status_code=400, detail="Invalid file type")
        result = await vector_store.save_file_to_vector_store(file, file_type)
        return {
            "message": "Vector Store has been updated",
            "details": result,
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

    initialised_graph = graph.with_config(
        configurable={
            "provider": query.provider,
            "model": query.model,
            "temperature": query.temperature,
        }
    )
    return await initialised_graph.ainvoke({"messages": [input_message]})


if __name__ == "__main__":
    query = Query(
        question="What is your name?",
        provider="google_genai",
        model="gemini-flash-2.0",
        temperature=0.5,
    )
    print(asyncio.run(generate(query)))
