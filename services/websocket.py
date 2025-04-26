import asyncio
import websockets
import json
from typing import Optional
from dependencies.auth import Auth
from config import settings
from urllib.parse import urlencode
import contextlib

class WebSocketService:
    _instance = None
    _websocket: Optional[any] = None
    _monitor_task: Optional[asyncio.Task] = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._auth = Auth()
        return cls._instance

    def __init__(self):
        self.base_url = settings.ws_api_url

    async def initialize(self):
        await self._auth.auth()

    async def connect(self):
        """Establish a websocket connection with current auth token."""
        await self._close_websocket()

        token = await self._auth.get_token()
        query_params = {"token": token}
        url_with_token = f"{self.base_url}/ws?{urlencode(query_params)}"

        try:
            self._websocket = await websockets.connect(url_with_token)
            print("[WebSocket] Connected")
        except Exception as e:
            print(f"[WebSocket] Failed to connect: {e}")
            raise

        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_connection())

    async def _close_websocket(self):
        """Safely close the websocket connection."""
        if self._websocket:
            with contextlib.suppress(Exception):
                await self._websocket.close()
            self._websocket = None

    async def _reconnect(self):
        """Reconnect logic."""
        print("[WebSocket] Reconnecting...")
        await self._close_websocket()
        await self._auth.auth()  # Force re-auth
        await self.connect()

    async def send_message(self, message: str):
        """Send a message, reconnect if sending fails."""
        try:
            await self._websocket.send(message)
            print(f"[WebSocket] Message sent: {message}")
        except Exception as e:
            print(f"[WebSocket] Send failed: {e}")
            await self._reconnect()

    async def receive_message(self):
        """Receive a message, reconnect if receiving fails."""
        try:
            response = await self._websocket.recv()
            try:
                message = json.loads(response)
                if message.get("type") == "token":
                    return message.get("value")
                return message
            except json.JSONDecodeError:
                return response
        except Exception as e:
            print(f"[WebSocket] Receive failed: {e}")
            await self._reconnect()
            return None

    async def _monitor_connection(self, interval=30):
        """Background monitor to check websocket health."""
        print("[WebSocket] Starting connection monitor...")
        while True:
            try:
                if self._websocket:
                    pong = await self._websocket.ping()
                    await asyncio.wait_for(pong, timeout=10)
            except Exception as e:
                print(f"[WebSocket] Connection lost in monitor: {e}")
                await self._reconnect()

            await asyncio.sleep(interval)

    async def close(self):
        """Gracefully shutdown websocket service."""
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(Exception):
                await self._monitor_task

        await self._close_websocket()
        print("WebSocketService closed.")
