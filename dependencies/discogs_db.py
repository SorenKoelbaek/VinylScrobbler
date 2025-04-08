import sqlite3
import os
from dependencies.log_setup import get_logger

logger = get_logger(__name__)

class DiscogsDB:
    """Handles storing and searching Discogs collection data in SQLite."""

    def __init__(self, db_path="discogs_collection.db"):
        self.db_path = db_path
        self._init_db()  # Ensure tables exist

    def _init_db(self):
        """Creates tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.executescript("""
                CREATE TABLE IF NOT EXISTS artists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE
                );

                CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    artist_id INTEGER,
                    FOREIGN KEY (artist_id) REFERENCES artists(id)
                );

                CREATE TABLE IF NOT EXISTS tracks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    album_id INTEGER,
                    FOREIGN KEY (album_id) REFERENCES albums(id)
                );
            """)
            conn.commit()
        logger.debug("✅ Database initialized and tables are ready.")

    def album_exists(self, artist_name, album_title):
        """Checks if an album is already stored in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT albums.id FROM albums
                JOIN artists ON albums.artist_id = artists.id
                WHERE artists.name = ? AND albums.title = ?
            """, (artist_name, album_title))

            result = cursor.fetchone()
            return result is not None  # True if album exists, False otherwise

    def store_album(self, artist_name, album_title, tracks):
        """Stores album data, ensuring artists & tracks are linked correctly."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Insert or get artist ID
            cursor.execute("INSERT OR IGNORE INTO artists (name) VALUES (?)", (artist_name,))
            cursor.execute("SELECT id FROM artists WHERE name = ?", (artist_name,))
            artist_id = cursor.fetchone()[0]

            # Insert album
            cursor.execute("INSERT OR IGNORE INTO albums (title, artist_id) VALUES (?, ?)", (album_title, artist_id))
            cursor.execute("SELECT id FROM albums WHERE title = ?", (album_title,))
            album_id = cursor.fetchone()[0]

            # Insert tracks
            for track in tracks:
                cursor.execute("INSERT OR IGNORE INTO tracks (name, album_id) VALUES (?, ?)", (track, album_id))

            conn.commit()
        logger.debug(f"📀 Stored album: {album_title} by {artist_name} with {len(tracks)} tracks.")

    def update_last_run(self, start=True):
        """Updates the last_run_start or last_run_end timestamp in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            if start:
                cursor.execute("INSERT OR REPLACE INTO last_update (id, last_run_start) VALUES (1, datetime('now'))")
                logger.debug("🕒 Recorded last_run_start timestamp.")
            else:
                cursor.execute("UPDATE last_update SET last_run_end = datetime('now') WHERE id = 1")
                logger.debug("🕒 Recorded last_run_end timestamp.")

            conn.commit()

    def get_last_update(self):
        """Retrieves the last run timestamps from the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_run_start, last_run_end FROM last_update WHERE id = 1")
            result = cursor.fetchone()
            return result if result else (None, None)

    def search_album_by_track(self, artist_name, track_name):
        """Finds an album in the collection that contains the given track by the given artist."""
        artist_name = artist_name.lower().replace("the ", "").strip()
        track_name = track_name.lower().strip()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT albums.title 
                FROM albums
                JOIN artists ON albums.artist_id = artists.id
                JOIN tracks ON tracks.album_id = albums.id
                WHERE LOWER(artists.name) LIKE '%' || ? || '%' 
                AND LOWER(tracks.name) = ?
                LIMIT 1
            """, (artist_name, track_name))

            result = cursor.fetchone()
            return result if result else None  # Return album title if found, otherwise None
