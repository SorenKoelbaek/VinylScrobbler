from dependencies.discogs_db import DiscogsDB
from dependencies.log_setup import get_logger
from config import settings
from datetime import datetime, timedelta
import discogs_client
import time
logger = get_logger(__name__)


class DiscogsCollection:
    """Caches Discogs collection & persists it in a database."""

    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DiscogsCollection, cls).__new__(cls)
            cls._instance.db = DiscogsDB()
            cls._instance.client = discogs_client.Client(
                "VinylScrobbler/1.0", user_token=settings.discogs_personal_token
            )
            cls._instance.last_refresh = None
            cls._instance._refresh_collection()
        return cls._instance

    def _refresh_collection(self):
        """Fetches user's Discogs collection & stores in DB (once a day)."""

        # ✅ Check last update time
        last_start, last_end = self.db.get_last_update()
        if last_end and (datetime.now() - datetime.strptime(last_end, "%Y-%m-%d %H:%M:%S")) < timedelta(days=1):
            logger.debug("⏳ Skipping refresh, last successful run was less than 24 hours ago.")
            return

        logger.debug("🔄 Fetching Discogs collection for daily refresh...")
        self.db.update_last_run(start=True)  # ✅ Set `last_run_start`

        try:
            user = self.client.identity()
            if not user:
                logger.warning("❌ Could not authenticate with Discogs.")
                return

            collection_items = user.collection_folders[0].releases
            total_items = len(collection_items)
            logger.debug(f"📦 Found {total_items} releases in collection.")

            request_count = 0  # ✅ Track API requests, not just albums

            for index, item in enumerate(collection_items, start=1):
                try:
                    request_count += 1  # ✅ Counting this enumeration as an API call

                    release = item.release
                    album_title = getattr(release, "title", None)
                    tracks = [track.title for track in getattr(release, "tracklist", [])]

                    if not album_title or not tracks:
                        logger.error(f"⚠️ Skipping invalid album (missing title or tracks): {release}")
                        continue  # Skip albums with missing data

                    for artist in release.artists:
                        artist_name = getattr(artist, "name", None)

                        if not artist_name:
                            logger.error(f"⚠️ Skipping album '{album_title}' due to missing artist info.")
                            continue  # Skip if artist name is missing

                        # ✅ Skip if album already exists
                        if self.db.album_exists(artist_name, album_title):
                            logger.debug(f"⏭️ Skipping existing album: '{album_title}' by '{artist_name}'.")
                            continue

                        self.db.store_album(artist_name, album_title, tracks)
                        logger.debug(f"📀 [{index}/{total_items}] Stored: '{album_title}' by '{artist_name}'.")

                        request_count += 1  # ✅ Additional API request for artist details

                    # ✅ Rate limiting: If we've made 50 requests, wait 60 seconds
                    if request_count >= 50:
                        logger.debug("⏳ Reached API limit (50 requests/min). Waiting 60 seconds...")
                        time.sleep(60)  # Wait before making more requests
                        request_count = 0  # Reset counter after wait

                except Exception as album_error:
                    logger.error(f"⚠️ Error processing album {index}/{total_items}: {album_error}")
                    continue  # Continue to next album even if one fails

            self.db.update_last_run(start=False)  # ✅ Set `last_run_end`
            self.last_refresh = datetime.now()
            logger.debug("✅ Collection refreshed and stored in database.")

        except Exception as e:
            logger.error(f"⚠️ Failed to fetch Discogs collection: {e}")


