# listener_state.py
import asyncio
from dependencies.log_setup import get_logger
from services.audio_listener import AudioListener

logger = get_logger(__name__)

class ListenerState:
    def __init__(self):
        self._active = False
        self._lock = asyncio.Lock()
        self._task: asyncio.Task | None = None
        self._listener = AudioListener()

    @property
    def active(self):
        return self._active

    async def set_active(self, value: bool):
        async with self._lock:
            if self._active == value:
                return  # No change

            self._active = value
            logger.info(f"🔁 ListenerState changed: {'Active' if value else 'Inactive'}")

            if value:
                # Start listener task
                logger.info("🎙️ Starting mic listener")
                self._task = asyncio.create_task(self._listener.start())
            else:
                # Stop listener and cancel task
                logger.info("🛑 Stopping mic listener")
                await self._listener.stop()
                if self._task:
                    self._task.cancel()
                    self._task = None
