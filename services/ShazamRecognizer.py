import asyncio
import os
from dependencies.log_setup import get_logger
from dependencies.PlaybackState import PlaybackState
from dependencies.ListenerState import ListenerState
from pathlib import Path
import ssl
import aiohttp
from uuid import uuid4
from shazamio import Shazam
from shazamio.interfaces.client import HTTPClientInterface
from aiohttp_retry import RetryClient, ExponentialRetry

logger = get_logger(__name__)

def build_shazam_url(language="en-US", endpoint_country="GB", device="android"):
    uuid_1 = str(uuid4())
    uuid_2 = str(uuid4())

    return (
        f"https://amp.shazam.com/discovery/v5/{language}/{endpoint_country}/{device}"
        f"/-/tag/{uuid_1}/{uuid_2}"
        "?sync=true&webv3=true&sampling=true"
        "&connected=&shazamapiversion=v3&sharehub=true"
        "&hubv5minorversion=v5.1&hidelb=true&video=v3"
    )

class InsecureHTTPClient(HTTPClientInterface):
    async def request(self, method, url, *args, **kwargs):
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        connector = aiohttp.TCPConnector(ssl=ssl_context)
        retry_options = ExponentialRetry(attempts=3)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with RetryClient(client_session=session, retry_options=retry_options) as client:
                if method.upper() == "GET":
                    async with client.get(url, **kwargs) as resp:
                        return await resp.json()
                elif method.upper() == "POST":
                    async with client.post(url, **kwargs) as resp:
                        return await resp.json()
                else:
                    raise ValueError("Unsupported HTTP method")

class ShazamRecognizer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ShazamRecognizer, cls).__new__(cls)
        return cls._instance

    def __init__(self, playback_state: PlaybackState = None, listener_state: ListenerState = None, input_dir="recordings", processed_dir="processed"):
        if not hasattr(self, "initialized"):
            self.input_dir = input_dir
            self.processed_dir = processed_dir
            os.makedirs(processed_dir, exist_ok=True)
            self.shazam = Shazam(http_client=InsecureHTTPClient())
            self.playback_state = playback_state
            self.listener_state = listener_state
            self.silence_count = 0

            logger.debug("ShazamRecognizer initialized.")
            self.initialized = True

    async def delete_file_safely(self, file_path: str):
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                logger.debug(f"🗑️ Deleted recording: {file_path}")
            else:
                logger.debug(f"⚠️ Tried to delete non-existent file: {file_path}")
        except Exception as e:
            logger.warning(f"❌ Error deleting recording {file_path}: {e}")

    def _cleanup_input_dir(self):
        for f in os.listdir(self.input_dir):
            if f.endswith(".wav"):
                try:
                    path = os.path.join(self.input_dir, f)
                    os.remove(path)
                    logger.debug(f"🧹 Deleted stale file on startup: {path}")
                except Exception as e:
                    logger.warning(f"❌ Could not delete stale file: {path} – {e}")

    async def recognize_audio(self, file_path):
        if not self.listener_state.active:
            logger.debug(f"🚫 Listener inactive — skipping {file_path}")
            await self.delete_file_safely(file_path)
            return

        try:
            logger.debug(f"🎧 Processing: {file_path}")

            import numpy as np
            import soundfile as sf

            audio_data, _ = sf.read(file_path)
            volume = np.sqrt(np.mean(np.square(audio_data)))
            silence_threshold = 0.01  # much more realistic

            logger.debug(f"Recorded file volume: {volume}")

            if volume < silence_threshold:
                logger.info(f"🔇 Detected silence for {file_path}, skipping Shazam call.")
                if self.playback_state.current and self.playback_state.current.state != "paused":
                    self.playback_state.current.state = "paused"
                    await self.playback_state._trigger_hook()
                    logger.debug("🔇 Local silence 3x → Paused playback")
                await self.delete_file_safely(file_path)
                return

            result = await self.shazam.recognize(file_path)

            logger.debug(f"result? {result}")
            if result.get("track"):
                self.silence_count = 0
                track_info = result["track"]
                album = track_info['sections'][0]['metadata'][0]['text']
                song = track_info.get("title", "Unknown")
                artist = track_info.get("subtitle", "Unknown Artist")

                await self.playback_state.update_track_metadata(
                    song_name=song,
                    album_name=album,
                    artist_name=artist,
                    source="Shazam",
                    spotify_track=None,
                    state="playing"
                )

                logger.debug(f"📻 Shazam updated playback: {song} – {artist} ({album})")
            else:
                self.silence_count += 1
                if self.silence_count >= 3:
                    if self.playback_state.current and self.playback_state.current.state != "paused":
                        self.playback_state.current.state = "paused"
                        await self.playback_state._trigger_hook()
                        logger.debug("🔇 Shazam: No match 2x → Paused playback")

            await self.delete_file_safely(file_path)

        except Exception as e:
            logger.error(f"❌ Error recognizing {file_path}: {e}")

    async def watch_folder(self, interval=5):
        logger.debug("📁 Shazam folder watcher started")
        while True:
            files = [f for f in os.listdir(self.input_dir) if f.endswith(".wav")]
            for file in files:
                file_path = os.path.join(self.input_dir, file)
                await self.recognize_audio(file_path)
            await asyncio.sleep(interval)

    async def start(self):
        self._cleanup_input_dir()
        logger.debug("🚀 Shazam recognizer started")
        await self.watch_folder()