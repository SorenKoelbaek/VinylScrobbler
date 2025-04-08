from dependencies.discogs_db import DiscogsDB
from dependencies.log_setup import get_logger
from config import settings
import discogs_client

logger = get_logger(__name__)

class DiscogsAPI:
    """Handles Discogs API & searches collection database."""

    def __init__(self):
        self.db = DiscogsDB()  # ✅ Use database
        self.token = settings.discogs_personal_token
        self.client = discogs_client.Client("VinylScrobbler/1.0", user_token=self.token)

    def search_album(self, artist, track, album):
        """Searches for albums in user's collection first, then Discogs API if enabled."""
        logger.debug(f"🔍 Searching for album: {artist} - {track}")

        # ✅ Step 1: Check local database first
        if settings.collection_first:
            local_albums = self.db.search_album_by_track(artist, track)
            if local_albums:
                logger.info(f"✅ Found {len(local_albums)} album(s) in local collection.")
                for local_album in local_albums:
                    if local_album == album:
                        return artist, local_album, True
                return artist, local_albums[0], True  # ✅ Return first local album

        # ✅ Step 2: Fallback to Discogs API if allowed
        return self._search_discogs(artist, track, album)

    def _search_discogs(self, artist, track, album):
        """Search Discogs for an album (if allowed)."""
        results = self.client.search(track, type="release", artist=artist)
        if results.count == 0:
            logger.info(f"No album found on Discogs for: {artist} - {track}")
            return artist, album, False

        # Get first Discogs result
        first_artist, first_album = results[0].artists[0].name, results[0].title
        logger.info(f"📀 Found album on Discogs: {first_album} by {first_artist}")
        return first_artist, first_album, False
