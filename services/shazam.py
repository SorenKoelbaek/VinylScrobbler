import asyncio
import os
from shazamio import Shazam
from datetime import datetime
from dependencies.log_setup import get_logger
from services.song import SongState

logger = get_logger(__name__)  # Use logging instead of print

class ShazamRecognizer:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(ShazamRecognizer, cls).__new__(cls)
        return cls._instance

    def __init__(self, input_dir="recordings", processed_dir="processed"):
        if not hasattr(self, "initialized"):
            self.input_dir = input_dir
            self.processed_dir = processed_dir
            os.makedirs(processed_dir, exist_ok=True)
            self.song_state = SongState()
            self.shazam = Shazam()  # Use Rust-based recognition

            logger.debug("ShazamRecognizer initialized.")
            self.initialized = True

    async def recognize_audio(self, file_path):
        """Uses ShazamIO to recognize an audio file and updates state only if it's a new song."""
        try:
            logger.debug(f"Processing: {file_path}")

            result = await self.shazam.recognize(file_path)

            if result.get("track"):
                track_info = result["track"]
                song = track_info.get("title", "Unknown")
                artist = track_info.get("subtitle", "Unknown Artist")
                _is_new = self.song_state.update_song(song, artist)

            else:
                logger.debug("No match found")

            os.remove(file_path)
            logger.debug(f"Deleted: {file_path}")

        except Exception as e:
            logger.error(f"Error recognizing {file_path}: {e}")

    async def watch_folder(self, interval=5):
        """Watches the folder for new WAV files and processes them."""
        while True:
            files = [f for f in os.listdir(self.input_dir) if f.endswith(".wav")]
            for file in files:
                file_path = os.path.join(self.input_dir, file)
                await self.recognize_audio(file_path)
            await asyncio.sleep(interval)

    async def start(self):
        """Starts the folder-watching task."""
        logger.debug("Shazam Recognizer started.")
        await self.watch_folder()
