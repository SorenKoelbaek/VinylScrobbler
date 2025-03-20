from dependencies.log_setup import get_logger
from dependencies.discogs_api import DiscogsAPI

logger = get_logger(__name__)

class SongState:
    """Keeps track of the last recognized song to avoid duplicate state updates."""
    _instance = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(SongState, cls).__new__(cls)
            cls._instance.last_song = None
            cls._instance.last_artist = None
            cls._instance.discogs = DiscogsAPI()
        return cls._instance

    def update_song(self, song, artist):
        """Updates the song state only if the song has changed."""
        if (song, artist) != (self.last_song, self.last_artist):
            found_artist, album, in_collection = self.discogs.search_album(artist, song)  # ✅ Get artist+album+collection

            if album:
                if in_collection:
                    logger.info(f"🔄 New song detected: {song} by {artist} from album '{album}' (✅ In collection)")
                else:
                    logger.info(f"🔄 New song detected: {song} by {artist} from album '{album}' (❌ Not in collection)")
            else:
                logger.info(f"🔄 New song detected: {song} by {artist} (album unknown)")

            self.last_song = song
            self.last_artist = artist
            return True
        else:
            logger.debug(f"🔁 Same song, skipping update: {song} by {artist}")
            return False
