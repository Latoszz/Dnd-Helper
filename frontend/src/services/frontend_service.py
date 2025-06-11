import json
from fastapi import HTTPException

import httpx

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

    async def post_data(self, endpoint_key: str ,payload: dict):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self._get_url(endpoint_key),
                    json=payload,
                    timeout=self.config['timeout']
                )
                response.raise_for_status()
                return response.json()['message']
        except (httpx.HTTPError, json.JSONDecodeError) as e:
            print(f"Error posting data: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Backend communication failed: {str(e)}"
            )
