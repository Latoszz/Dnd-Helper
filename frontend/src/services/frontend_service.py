import json
from fastapi import HTTPException

import httpx
from streamlit.runtime.uploaded_file_manager import UploadedFile


class FrontendService:
    def __init__(self, configManager):
        self.config = configManager.get_config().get('backend', {})
        self.client = httpx.AsyncClient()


    def _get_url(self, endpoint_key: str) -> str:
        return f"{self.config['base_url']}{self.config['endpoints'][endpoint_key]}"

    async def get_data(self, endpoint_key: str):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self._get_url(endpoint_key),
                    timeout=self.config['timeout']
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Error fetching data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Backend communication failed: {str(e)}"
            )

    async def post_data(self, endpoint_key: str ,payload: dict,files: dict = None):
        try:
            async with httpx.AsyncClient() as client:
                request_params = {
                    "url": self._get_url(endpoint_key),
                    "timeout": self.config['timeout']
                }

                if files:
                    request_params["files"] = files
                if payload and not files:
                    request_params["json"] = payload
                elif payload and files:
                    request_params["data"] = payload

                response = await client.post(**request_params)
                response.raise_for_status()
                return response.json()['message']
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Error posting data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Backend communication failed: {str(e)}"
            )
    async def post_file(self, endpoint_key: str,uploadedFile: UploadedFile):
        try:
            async with httpx.AsyncClient() as client:

                response = await client.post(
                    self._get_url(endpoint_key),
                    files={"file":uploadedFile},
                    timeout=self.config['timeout']
                )
                response.raise_for_status()
                return response.json()

        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Error uploading file: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )

    async def stream_data(self, endpoint_key: str, payload: dict):
        """New streaming method for LangGraph/LangChain responses"""
        try:
            async with httpx.AsyncClient() as client:
                request_params = {
                    "url": self._get_url(endpoint_key),
                    "json": payload,
                    "timeout": self.config.get('timeout', 30.0),
                    "headers": {"Accept": "text/event-stream"}  # For SSE
                }

                async with client.stream("POST", **request_params) as response:
                    response.raise_for_status()

                    # Handle different streaming formats
                    if response.headers.get("content-type", "").startswith("text/event-stream"):
                        # Server-Sent Events format
                        async for chunk in self._parse_sse_stream(response):
                            yield chunk
                    else:
                        # JSON streaming format (one JSON object per line)
                        async for chunk in self._parse_json_stream(response):
                            yield chunk

        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Error streaming data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Backend streaming failed: {str(e)}"
            )

    async def _parse_sse_stream(self, response):
        """Parse Server-Sent Events stream"""
        async for line in response.aiter_lines():
            if line.startswith("data: "):
                data = line[6:]  # Remove "data: " prefix
                if data == "[DONE]":
                    break
                try:
                    chunk_data = json.loads(data)
                    # Extract content based on your LangGraph response format
                    if "content" in chunk_data:
                        yield chunk_data["content"]
                    elif "message" in chunk_data:
                        yield chunk_data["message"]
                    elif isinstance(chunk_data, str):
                        yield chunk_data
                except json.JSONDecodeError:
                    # If not JSON, yield raw data
                    yield data

    async def _parse_json_stream(self, response):
        """Parse JSON stream (one JSON object per line)"""
        async for line in response.aiter_lines():
            if line.strip():
                try:
                    chunk_data = json.loads(line)
                    # Extract content based on your LangGraph response format
                    if "content" in chunk_data:
                        yield chunk_data["content"]
                    elif "message" in chunk_data:
                        yield chunk_data["message"]
                    elif "delta" in chunk_data and "content" in chunk_data["delta"]:
                        yield chunk_data["delta"]["content"]
                    elif isinstance(chunk_data, str):
                        yield chunk_data
                except json.JSONDecodeError:
                    # If not JSON, yield raw line
                    yield line


