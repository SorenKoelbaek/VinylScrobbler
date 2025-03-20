import asyncio
import argparse
from dependencies.dicsogs_collection import DiscogsCollection
from services.audio_listener import AudioListener
from services.shazam import ShazamRecognizer
from dependencies.log_setup import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)
from config import settings

async def main(reinitialize=False):
    """Main entry point of the application."""
    logger.info("🚀 Starting application...")

    # ✅ Step 1: Initialize Discogs collection
    discogs_collection = DiscogsCollection()

    # ✅ Step 2: Check last refresh timestamp
    last_start, last_end = discogs_collection.db.get_last_update()

    needs_refresh = (
            reinitialize or
            not last_end or  # If last_end is missing, assume we need a refresh
            (datetime.now() - datetime.strptime(last_end, "%Y-%m-%d %H:%M:%S")) >= timedelta(days=1)  # Refresh if >24h
    )

    if needs_refresh:
        logger.info("🔄 Updating Discogs collection...")
        discogs_collection._refresh_collection()
        if reinitialize:
            logger.info("✅ Reinitialization complete. Exiting...")
            return  # If manually reinitializing, exit after update

    logger.info("✅ Discogs collection is up-to-date.")

    # ✅ Step 3: Start audio processing services only after Discogs collection is ready
    audio_listener = AudioListener()
    shazam_recognizer = ShazamRecognizer()

    await asyncio.gather(
        audio_listener.start(settings.wait_seconds),
        shazam_recognizer.start()
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VinylScrobbler")
    parser.add_argument("--reinit", action="store_true", help="Force reinitialize Discogs collection and exit")
    args = parser.parse_args()

    asyncio.run(main(reinitialize=args.reinit))
