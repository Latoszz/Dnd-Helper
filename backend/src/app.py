from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from httpx import AsyncClient
import logging
from models.request import Request
from managers.config_manager import Config
import logging


config = Config("src/config/config.yaml")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # logging.info("Starting up")
    # logging.info(config.config)
    app.state.client = AsyncClient(
        base_url=config.get_value("ai_service_link"), timeout=60.0
    )
    yield
    # logging.info("Shutting down")
    await app.state.client.aclose()


app = FastAPI(lifespan=lifespan)

FastAPI(lifespan=lifespan)


def get_http_client() -> AsyncClient:
    return app.state.client


@app.post("/chat")
async def chit_chat(request: Request):
    try:
        client = get_http_client()
        async with client.stream(
            "POST",
            url="/generate",
            json={
                "question": request.question,
                "provider": request.provider,
                "model": request.model,
                "temperature": request.temperature,
            },
        ) as response:

            async def gen():
                try:
                    async for chunk in response.aiter_lines():
                        yield chunk
                except Exception as e:
                    logging.error(e)
                    yield f"\n\n[Error]: {str(e)}\n"

            return StreamingResponse(gen(), media_type="text/plain")
    except Exception as e:
        logging.error(e)
        return "ERROR"

    # logging.info(response)
    # data = response.json()
    # logging.info(data)
    # if response.status_code == 500:
    #     return {
    #         "message": "Currently we have internal issues :)",
    #         "detail": data["detail"],
    #     }

    # ai_responses = [
    #     msg["content"] for msg in data["messages"] if msg.get("type") == "ai"
    # ]
    # last_two_responses = ai_responses[-2:] if len(ai_responses) >= 2 else ai_responses
    # return {"message": "\n\n".join(last_two_responses)}
