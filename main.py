import asyncio
import argparse
from dependencies.dicsogs_collection import DiscogsCollection
from services.audio_listener import AudioListener
from services.shazam import ShazamRecognizer
from dependencies.log_setup import get_logger

logger = get_logger(__name__)

async def main(reinitialize=False):
    """Main entry point of the application."""
    logger.debug("🚀 Starting application...")

    # ✅ Step 1: Initialize Discogs collection (forced refresh if reinitialize=True)
    discogs_collection = DiscogsCollection()
    if reinitialize:
        logger.debug("🔄 Reinitializing Discogs collection...")
        discogs_collection._refresh_collection()
        logger.debug("✅ Reinitialization complete. Exiting...")
        return  # Exit after refreshing collection

    if discogs_collection.last_refresh is None:
        logger.debug("🔄 Waiting for Discogs collection to populate before starting services...")
        await asyncio.sleep(10)  # Give time for collection to populate

    # ✅ Step 2: Start audio processing services only after Discogs collection is ready
    audio_listener = AudioListener()
    shazam_recognizer = ShazamRecognizer()

    await asyncio.gather(
        audio_listener.start(),
        shazam_recognizer.start()
    )

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VinylScrobbler")
    parser.add_argument("--reinit", action="store_true", help="Force reinitialize Discogs collection and exit")
    args = parser.parse_args()

    asyncio.run(main(reinitialize=args.reinit))
