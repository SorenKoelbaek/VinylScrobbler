import asyncio
from dataclasses import dataclass
from typing import Optional
from dependencies.log_setup import get_logger
from config import settings
from services.websocket import WebSocketService
logger = get_logger(__name__)
import json

@dataclass
class ConnectUpdate:
    state: str
    device_id: str
    device_name: str
    self_active: bool
    spotify_track: Optional[str] = None
    song_name: Optional[str] = None
    album_name: Optional[str] = None
    artist_name: Optional[str] = None
    source: Optional[str] = None  # New field to track the source (Spotify/Shazam)


class PlaybackState:
    def __init__(self, on_update=None, websocket: Optional[WebSocketService] = None):
        self.current: Optional[ConnectUpdate] = None
        self.previous_track: Optional[str] = None
        self.on_update = on_update
        self.previous_state: Optional[str] = None
        self.previous_track_id: Optional[str] = None
        self.previous_device_id: Optional[str] = None
        self.websocket = websocket

    async def _trigger_hook(self):
        if self.on_update and self.current:
            if asyncio.iscoroutinefunction(self.on_update):
                await self.on_update(self.current)
            else:
                self.on_update(self.current)

        if not self.current:
            return

        payload = {}
        changed = False  # Track if any changes occurred

        # 🔁 Track changes
        current_state = self.current.state
        current_track_id = self.current.spotify_track or self.current.song_name or "unknown"
        payload["state"] = current_state

        # 🟡 Playback state
        if current_state != self.previous_state:
            self.previous_state = current_state
            changed = True
            logger.info("▶️ Playback started" if current_state == "playing"
                        else "⏸️ Playback paused" if current_state == "paused"
                        else "⏹️ Playback stopped" if current_state == "stopped"
                        else f"ℹ️ Playback state changed: {current_state}")

        # 🟢 Track change
        if current_track_id != self.previous_track_id:
            self.previous_track_id = current_track_id
            changed = True
            if self.current.song_name:
                logger.info(
                    f"🎶 Now playing: {self.current.song_name} – {self.current.artist_name} ({self.current.album_name})")

        payload["track"] = {
            "song_name": self.current.song_name,
            "artist_name": self.current.artist_name,
            "album_name": self.current.album_name,
            "spotify_track": self.current.spotify_track,
        }

        # 🔁 Device change
        if self.current.device_id != self.previous_device_id:
            self.previous_device_id = self.current.device_id
            changed = True

        # 📡 Send via WebSocket if something changed
        payload["device"] = {
            "device_id": self.current.device_id,
            "device_name": self.current.device_name,
        }
        payload["source"] = self.current.source
        if self.websocket and changed:
            await self.websocket.send_message(json.dumps({
                "type": "playback_update",
                "payload": payload
            }))


    async def update_from_connect(self, update: ConnectUpdate) -> bool:
        is_new_track = False

        if self.current is None:
            self.current = update
            is_new_track = True
        else:
            if self.current.spotify_track != update.spotify_track:
                is_new_track = True
            self.current.spotify_track = update.spotify_track
            self.current.state = update.state
            self.current.device_id = update.device_id
            self.current.device_name = update.device_name
            self.current.self_active = update.self_active

        await self._trigger_hook()
        return is_new_track

    async def update_track_metadata(
            self,
            spotify_track: Optional[str],
            song_name: Optional[str],
            album_name: Optional[str],
            artist_name: Optional[str],
            source: str,
            state: str,
            device_id: Optional[str] = None,
            device_name: Optional[str] = None,
            self_active: Optional[bool] = None,
    ):
        if self.current is None:
            self.current = ConnectUpdate(
                spotify_track=spotify_track,
                state=state,
                device_id=device_id or "this_device",
                device_name=device_name or "MyPythonLibrespot",
                self_active=self_active if self_active is not None else True,
                song_name=song_name,
                album_name=album_name,
                artist_name=artist_name,
                source=source,
            )
        else:
            self.current.spotify_track = spotify_track
            self.current.song_name = song_name
            self.current.album_name = album_name
            self.current.artist_name = artist_name
            self.current.state = state
            self.current.source = source
            if device_id:
                self.current.device_id = device_id
            if device_name:
                self.current.device_name = device_name
            if self_active is not None:
                self.current.self_active = self_active

        await self._trigger_hook()

    async def update_from_player_event(self, event_type: str, track_uri: str, position_ms: int):
        if self.current is None:
            self.current = ConnectUpdate(
                spotify_track=track_uri,
                state=event_type.lower(),
                device_id="this_device",
                device_name="MyPythonLibrespot",
                self_active=True,
            )
        else:
            self.current.spotify_track = track_uri
            self.current.state = event_type.lower()

        await self._trigger_hook()

    def __str__(self):
        return f"🎧 {self.current}"
