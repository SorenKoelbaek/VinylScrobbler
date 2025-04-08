import asyncio
import websockets
import json
from typing import Optional
from dependencies.auth import Auth
from config import settings
from urllib.parse import urlencode

class WebSocketService:
    _instance = None
    _websocket: Optional[any] = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._auth = Auth()
        return cls._instance

    def __init__(self):
        self.base_url = settings.ws_api_url   # Change this to your FastAPI backend URL

    async def initialize(self):
        await self._auth.auth()

    async def connect(self):
        """Connect to the WebSocket server with token as a query parameter."""
        # Close and discard previous websocket if it exists
        if self._websocket is not None:
            try:
                await self._websocket.close()
            except Exception:
                pass
            self._websocket = None
        # Prepare token query
        token = await self._auth.get_token()
        query_params = {"token": token}
        url_with_token = f"{self.base_url}/ws?{urlencode(query_params)}"

        # Create new connection
        self._websocket = await websockets.connect(url_with_token)
    async def send_message(self, message: str):
        """Send a message to the WebSocket server."""
        if self._websocket is None:
            raise Exception("WebSocket not connected. Please call connect() first.")
        await self._websocket.send(message)
        print(f"Message sent: {message}")

    async def receive_message(self):
        """Receive a message from the WebSocket server and extract the token."""
        if self._websocket is None:
            raise Exception("WebSocket not connected. Please call connect() first.")

        response = await self._websocket.recv()

        try:
            message = json.loads(response)
            if message.get("type") == "token":
                return message.get("value")
            return message
        except json.JSONDecodeError:
            return response  # fallback if message is plain text

    async def close(self):
        """Close the WebSocket connection."""
        if self._websocket:
            await self._websocket.close()
            print("WebSocket connection closed.")