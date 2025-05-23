import os
import wave
import asyncio
import sounddevice as sd
from datetime import datetime
from dependencies.log_setup import get_logger
from config import settings
from dependencies.database import get_settings
logger = get_logger(__name__)



class AudioListener:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AudioListener, cls).__new__(cls)
        return cls._instance

    def __init__(self, output_dir="recordings", sample_rate=44100, channels=1):
        if not hasattr(self, "initialized"):
            self.output_dir = output_dir
            self.sample_rate = sample_rate
            self.channels = channels
            os.makedirs(output_dir, exist_ok=True)

            logger.debug("AudioListener initialized.")
            self.initialized = True

    async def record_audio(self, duration=4):
        """Records audio for a given duration and saves it as WAV."""
        db_settings = await get_settings()
        try:

            input_name = db_settings.sound_input_device_name
            for i, dev in enumerate(sd.query_devices()):
                if dev["name"] == input_name:
                    sd.default.device = i
                    break

            logger.debug(f"Recording {duration}s of audio...")
            audio_data = sd.rec(
                int(self.sample_rate * duration),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            wav_filename = os.path.join(self.output_dir, f"{timestamp}.wav")

            # Save as WAV
            with wave.open(wav_filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())

            logger.debug(f"Saved: {wav_filename}")

        except Exception as e:
            logger.error(f"Error recording audio: {e}")

    async def start(self, interval=10):
        """Continuously records audio at set intervals."""
        db_settings = await get_settings()
        logger.debug("AudioListener started.")
        while True:
            await self.record_audio(db_settings.listen_length)
            await asyncio.sleep(db_settings.listen_interval)

    async def stop(self):
        """Stop the audio listener."""
        logger.debug("AudioListener stopped.")
