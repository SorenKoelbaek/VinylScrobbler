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
        if self._websocket:
            await self._close_websocket()

        token = await self._auth.get_token()
        query_params = {"token": token}
        url_with_token = f"{self.base_url}/ws?{urlencode(query_params)}"

        try:
            self._websocket = await websockets.connect(url_with_token)
        except Exception as e:
            print(f"[WebSocket] Failed to connect: {e}")
            raise

        # If connection succeeds, launch monitor if not running
        if not self._monitor_task or self._monitor_task.done():
            self._monitor_task = asyncio.create_task(self._monitor_connection())

    async def _close_websocket(self):
        """Safely close the websocket connection."""
        try:
            if self._websocket:
                await self._websocket.close()
        except Exception:
            pass
        finally:
            self._websocket = None

    async def _reconnect(self):
        """Reconnect logic."""
        await self._close_websocket()
        await self._auth.auth()  # Force re-auth
        await self.connect()

    async def send_message(self, message: str):
        """Send a message with resilience."""
        try:
            if not self._websocket or self._websocket.closed:
                await self._reconnect()

            await self._websocket.send(message)
            print(f"Message sent: {message}")
        except Exception as e:
            print(f"[WebSocket] Send failed: {e}")
            await self._reconnect()

    async def receive_message(self):
        """Receive a message with resilience."""
        try:
            if not self._websocket or self._websocket.closed:
                await self._reconnect()

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
            return None  # Returning None to avoid crash chains

    async def _monitor_connection(self, interval=30):
        """Background monitor to check websocket health."""
        print("[WebSocket] Starting connection monitor...")
        while True:
            try:
                if self._websocket and not self._websocket.closed:
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

