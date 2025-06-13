import logging
import json
from typing import cast
from fastapi import FastAPI, HTTPException
from fastapi import UploadFile
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from langgraph.graph.state import CompiledStateGraph
from langchain_core.messages import HumanMessage, AIMessage
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


@app.post("/chat")
async def generate(query: Query):
    graph = get_langgraph()
    input_message = HumanMessage(content=query.question)
    logger.info(f"Input message: {input_message}")

    # Configure the graph with your settings
    initialised_graph = graph.with_config(
        configurable={
            "provider": query.provider,
            "model": query.model,
            "temperature": query.temperature,
        }
    )

    async def generate_stream():
        try:
            async for event in initialised_graph.astream_events(
                {"messages": [input_message]},
                version="v2",
            ):
                event_type = event["event"]
                event_name = event.get("name", "")

                logger.debug(f"Event: {event_type}, Name: {event_name}")

                # Handle LLM model streaming chunks
                if event_type == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    logger.debug(chunk)
                    # OpenAI-compatible style
                    if hasattr(chunk, "content") and chunk.content:
                        payload = json.dumps({"content": chunk.content})
                        yield f"data: {payload}\n\n"
                    elif (
                        hasattr(chunk, "delta")
                        and hasattr(chunk.delta, "content")
                        and chunk.delta.content
                    ):
                        payload = json.dumps({"content": chunk.delta.content})
                        yield f"data: {payload}\n\n"

                # Handle LangGraph chain/node streaming
                elif event_type == "on_chain_stream":
                    if event_name in [
                        # "general",
                        # "advisor",
                        # # "creator",
                        # "bestiary",
                        # "combat",
                        "review",
                    ]:
                        chunk = event["data"].get("chunk")
                        logger.debug(f"Chunk data: {chunk}")

                        if chunk and "messages" in chunk:
                            for message in chunk["messages"]:
                                content = message.content
                                if content:
                                    payload = json.dumps({"content": content})
                                    yield f"data: {payload}\n\n"

                # Handle final output if not streamed
                elif event_type == "on_chain_end":
                    if event_name in [
                        # "general",
                        # "advisor",
                        # # "creator",
                        # "bestiary",
                        # "combat",
                        "review",
                    ]:
                        output = event["data"].get("output")
                        if output and hasattr(output, "content") and output.content:
                            for line in output.content.splitlines():
                                if line.strip():
                                    payload = json.dumps({"content": line + "\n"})
                                    yield f"data: {payload}\n\n"

            # Signal end of stream
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {str(e)}")
            error_payload = json.dumps({"error": str(e)})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )


# @app.post("/chat")
# async def generate(query: Query):
#     graph = get_langgraph()
#     input_message = HumanMessage(content=query.question)
#     logger.info(input_message)

#     initialised_graph = graph.with_config(
#         configurable={
#             "provider": query.provider,
#             "model": query.model,
#             "temperature": query.temperature,
#         }
#     )
#     result = await initialised_graph.ainvoke({"messages": [input_message]})

#     # Extract only AI messages that came from review agent
#     review_messages = [
#         m.content
#         for m in result.get("messages", [])
#         if isinstance(m, AIMessage) and m.name == "review"
#     ]

#     return review_messages


# if __name__ == "__main__":
#     query = Query(
#         question="What is your name?",
#         provider="google_genai",
#         model="gemini-flash-2.0",
#         temperature=0.5,
#     )
#     print(asyncio.run(generate(query)))
