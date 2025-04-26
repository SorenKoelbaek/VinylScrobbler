import argparse
import os
from services.ShazamRecognizer import ShazamRecognizer
from dependencies.log_setup import get_logger
from services.websocket import WebSocketService
from services.LibrespotService import LibrespotService
from dependencies.ListenerState import ListenerState
from dependencies.PlaybackState import PlaybackState, ConnectUpdate
from dependencies.spotify_api import SpotifyAPI
from dependencies.system_state import set_state, SystemStatus
from dependencies.database import (get_settings, SettingsData)
import asyncio
from asyncio import TaskGroup

logger = get_logger(__name__)
task_group: TaskGroup | None = None  # Global reference

async def main():
    logger.info("🚀 Starting main control loop...")
    db_settings = await get_settings()

    while True:
        try:
            await run_services(db_settings)
        except asyncio.CancelledError:
            logger.warning("🛑 Cancelled. Shutting down.")
            break
        except Exception as e:
            logger.error(f"🔥 Uncaught error: {e}")
            set_state(SystemStatus.ERROR)
        logger.info("🔁 Restarting services in 10 seconds...")
        await asyncio.sleep(10)


async def run_services(db_settings: SettingsData):
    """Main entry point of the application."""
    global task_group
    listener_state = ListenerState()  # Move to outer scope for shutdown access
    librespot_service = None
    shazam_recognizer = None

    try:
        websocket = WebSocketService()
        await websocket.initialize()

        # Retry until we get a valid Spotify token
        while True:
            try:
                set_state(SystemStatus.IDLE)
                websocket = WebSocketService()
                await websocket.initialize()
                await websocket.connect()
                spotify_token = await asyncio.wait_for(websocket.receive_message(), timeout=5)
                if not spotify_token:
                    raise Exception("No token received.")
                break
            except Exception as e:
                logger.error(f" Host unavailable, waiting")
                await asyncio.sleep(10)

        logger.info("🟢 Application starting services...")
        set_state(SystemStatus.RUNNING)

        spotify_api = SpotifyAPI(spotify_token)
        playback = await spotify_api.get_current_playback()
        playback_state = PlaybackState(websocket=websocket)

        if playback and playback.get("is_playing"):
            device = playback.get("device", {})
            await listener_state.set_active(False)
            await playback_state.update_track_metadata(
                spotify_track=playback["item"]["uri"],
                song_name=playback["item"]["name"],
                album_name=playback["item"]["album"]["name"],
                artist_name=playback["item"]["artists"][0]["name"],
                source="Spotify",
                state="playing",
                device_id=device.get("id", "boot_check"),
                device_name=device.get("name", "Spotify Boot"),
                self_active=False,
            )
        else:
            await listener_state.set_active(True)

        librespot_service = LibrespotService(
            name=db_settings.device_name,
            key=spotify_token,
            listener_state=listener_state,
            playback_state=playback_state,
        )
        shazam_recognizer = ShazamRecognizer(
            listener_state=listener_state,
            playback_state=playback_state,
        )

        async def librespot_wrapper():
            try:
                await librespot_service.start()
            except Exception as e:
                logger.error(f"🔥 LibrespotService.start failed: {e}")
                # optionally capture stderr:
                if librespot_service.process:
                    out = await librespot_service.process.communicate()
                    logger.error(f"Librespot stderr: {out[1] if len(out)>1 else out[0]}")
                raise

        async def shazam_wrapper():
            try:
                await shazam_recognizer.start()
            except Exception as e:
                logger.error(f"🔥 ShazamRecognizer.start failed: {e}")
                raise

        async with TaskGroup() as tg:
            task_group = tg
            tg.create_task(librespot_wrapper())
            tg.create_task(shazam_wrapper())

    except asyncio.CancelledError:
        logger.warning("🛑 TaskGroup received cancellation.")
        raise
    except Exception as e:
        logger.error(f"🔥 Service crashed: {e}")
        set_state(SystemStatus.ERROR)
        await asyncio.sleep(10)
    finally:
        logger.info("🔇 Deactivating listener...")
        await listener_state.set_active(False)
        if librespot_service:
            await librespot_service.stop()
        set_state(SystemStatus.IDLE)
