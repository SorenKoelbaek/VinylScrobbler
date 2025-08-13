# librespot_service.py
import asyncio
import os
from pathlib import Path
from dependencies.log_setup import get_logger
from dependencies.PlaybackState import PlaybackState, ConnectUpdate
from dependencies.spotify_api import SpotifyAPI
from dependencies.ListenerState import ListenerState
import re
from config import settings
from typing import Optional
import subprocess
import platform
from dependencies.database import get_settings
import websockets

system = platform.system()
logger = get_logger(__name__)

class LibrespotService:
    def __init__(self, name: str, key: str, listener_state: ListenerState, playback_state: PlaybackState):
        self.name = name
        self.key = key
        self.listener_state = listener_state  # Injected ListenerState
        self.binary_path = Path(__file__).resolve().parent.parent / "lib" / "release" / "librespot"
        self.process = None
        self.state = playback_state  # use shared state
        self.spotify_api = SpotifyAPI(self.key)

    async def resolve_pulseaudio_device(self, device_name: str) -> str | None:
        """Resolve a human-readable device name to a PulseAudio sink name."""
        try:
            sinks = subprocess.check_output(["pactl", "list", "short", "sinks"]).decode()
            detailed = subprocess.check_output(["pactl", "list", "sinks"]).decode()

            for line in sinks.strip().split('\n'):
                parts = line.split('\t')
                if len(parts) >= 2:
                    sink_name = parts[1]
                    if device_name.lower() in detailed.lower() and sink_name in detailed:
                        return sink_name
        except Exception as e:
            return None
        return None

    async def stop(self):
        if self.process and self.process.returncode is None:
            logger.info("🛑 Terminating librespot subprocess...")
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                logger.warning("⛔ Librespot did not terminate, killing...")
                self.process.kill()

    async def start(self):
        env = os.environ.copy()
        env["RUST_LOG"] = "error"

        db_settings = await get_settings()
        raw_out = (db_settings.sound_output_device_name or "").strip()

        def is_alsa_pcm(s: str) -> bool:
            return s.startswith(("hw:", "plughw:", "front:", "dmix:", "iec958:", "sysdefault:")) or "CARD=" in s

        backend = "rodio"
        device = None
        # Use system default for "default" or any ALSA PCM; otherwise pass the name.
        if raw_out and raw_out.lower() != "default" and not is_alsa_pcm(raw_out):
            device = raw_out

        logger.info(f"Using {backend} sink '{device or 'system default'}'")

        cmd = [
            str(self.binary_path),
            "-n", self.name,
            "-k", self.key,
            "--backend", backend,
            "--bitrate", "320",
            "--disable-audio-cache",
        ]
        if device:
            cmd += ["--device", device]

        logger.info(" ".join(cmd))

        self.process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=str(Path(__file__).resolve().parent.parent),
            env=env,
        )
        await self._stream_output()

    async def _stream_output(self):
        assert self.process.stdout is not None
        async for line in self.process.stdout:
            line_str = line.decode().strip()
            parsed = None
            logger.warning(f"⚠️ Got an event from Librespot: {line_str}")
            # CONNECT_UPDATE DISPATCH

            if line_str.startswith("[connect_update] "):
                if "state=playing" in line_str:
                    parsed = self._parse_connect_resume(line_str)
                elif "state=paused" in line_str:
                    parsed = self._parse_connect_pause(line_str)

            # PLAYER EVENTS DISPATCH
            elif line_str.startswith("PlayerEvent: TrackChanged"):
                parsed = self._parse_player_new_track(line_str)

            elif line_str.startswith("PlayerEvent: Playing"):
                parsed = self._parse_player_resume(line_str)

            elif line_str.startswith("PlayerEvent: Paused"):
                parsed = self._parse_player_pause(line_str)

            elif line_str.startswith("PlayerEvent: Stopped"):
                parsed = self._parse_player_pause(line_str)

            if parsed:
                # If metadata is missing (connect_update), try to enrich via API
                if (
                        parsed.get("source") == "Spotify"
                        and self.spotify_api
                        and parsed.get("spotify_track")
                        and not all(parsed.get(k) for k in ("song_name", "artist_name", "album_name"))
                ):
                    track_id = parsed["spotify_track"].split(":")[-1]
                    info = await self.spotify_api.get_track_info(track_id)
                    if info:
                        parsed["song_name"] = info["name"]
                        parsed["album_name"] = info["album"]["name"]
                        parsed["artist_name"] = info["artists"][0]["name"]

                # ❗ After enrichment, if still missing anything, SKIP the update
                if not all(parsed.get(k) for k in ("song_name", "album_name", "artist_name", "spotify_track")):
                    logger.warning(f"⚠️ Skipping update due to missing metadata: {parsed}")
                    continue

                try:
                    await self.state.update_track_metadata(**parsed)
                    await self._on_state_update(parsed["state"], parsed["source"], parsed["self_active"])
                except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as e:
                    logger.warning(f"WebSocket closed during librespot streaming: {e}")
                    break  # stop reading lines and let your TaskGroup tear down


    async def _on_state_update(self, state: str, source: str, active: bool):
        if source == "Spotify":
            if state == "playing":
                logger.info("🎶 Spotify playback resumed")
                await self.listener_state.set_active(False)
            else:
                logger.info("🎶 Spotify playback paused")
                await self.listener_state.set_active(True)

    def _parse_connect_update(self, line: str) -> Optional[dict]:
        try:
            data_str = line[len("[connect_update] "):]
            parts = {}
            for part in data_str.split():
                if "=" in part:
                    k, v = part.split("=", 1)
                    parts[k] = v
                else:
                    logger.error(f"⚠️ Skipping malformed connect_update part: '{part}'")

            return {
                "spotify_track": parts["uri"],
                "state": parts["state"],
                "device_id": parts["device_id"],
                "device_name": parts["device_name"],
                "self_active": parts["self_active"].lower() == "true",
                "source": "Spotify",
            }
        except Exception as e:
            logger.error(f"❌ Failed to parse connect_update line: {line}\n{e}")
            return None

    def _parse_natural_stop(self, line: str) -> Optional[dict]:
        parsed = self._parse_connect_update(line)
        if parsed and parsed["state"] == "playing":
            return parsed
        return None

    def _parse_connect_resume(self, line: str) -> Optional[dict]:
        parsed = self._parse_connect_update(line)
        if parsed and parsed["state"] == "playing":
            return parsed
        return None

    def _parse_connect_pause(self, line: str) -> Optional[dict]:
        parsed = self._parse_connect_update(line)
        if parsed and parsed["state"] == "paused":
            return parsed
        return None

    def _parse_connect_new_track(self, line: str) -> Optional[dict]:
        # Treated the same as resume but typically with a new track URI
        return self._parse_connect_resume(line)

    def _parse_player_resume(self, line: str) -> Optional[dict]:
        match = re.search(r'SpotifyId\("([^"]+)"\)', line)
        if match:
            return {
                "spotify_track": match.group(1),
                "state": "playing",
                "source": "Spotify",
                "self_active": True,
            }
        return None

    def _parse_player_pause(self, line: str) -> Optional[dict]:
        match = re.search(r'SpotifyId\("([^"]+)"\)', line)
        if match:
            return {
                "spotify_track": match.group(1),
                "state": "paused",
                "source": "Spotify",
                "self_active": True,
            }
        return None

    def _parse_player_new_track(self, line: str) -> Optional[dict]:
        try:
            uri_match = re.search(r'uri: "([^"]+)"', line)
            name_match = re.search(r'name: "([^"]+)",', line)
            album_match = re.search(r'album: "([^"]+)",', line)
            artist_match = re.search(r'ArtistWithRole {.*?name: "([^"]+)"', line)

            return {
                "spotify_track": uri_match.group(1),
                "song_name": name_match.group(1),
                "album_name": album_match.group(1),
                "artist_name": artist_match.group(1),
                "state": "playing",
                "source": "Spotify",
                "self_active": True,
            }
        except Exception as e:
            logger.error(f"❌ Failed to parse TrackChanged: {e}")
            return None
