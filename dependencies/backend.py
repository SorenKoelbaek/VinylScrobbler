import requests
from typing import Optional
import logging
from dependencies.auth import Auth
from config import settings
import logging
logger = logging.getLogger(__name__)

class Backend:
    _instance = None
    _auth: Optional[Auth] = None

    def __new__(cls, auth_token: Optional[str] = None):
        if not cls._instance:
            cls._instance = super().__new__(cls)
            cls._auth = Auth()
        return cls._instance

    def __init__(self):
        self.base_url = settings.api_url  # Your FastAPI backend URL
        self.session = requests.Session()

    async def initialize(self):
        await self._auth.auth()

    async def get_auth_token(self) -> Optional[str]:
        """Get the current auth token."""

        return await self._auth.get_token()

    async def search_song(self, song, artist, album):
        url = f"{self.base_url}/music/search/?track_name={song}&artist_name={artist}&album_name={album}'"
        token = await self._auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}"  # Add the Bearer token in the headers
        }
        logger.info(f"Searching song {song} in {url}")
        # Send GET request with the Bearer token
        response = self.session.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()  # Return the JSON response
        else:
            raise Exception(f"Failed to fetch song: {response.status_code} {response.text}")

    async def get_collection(self,):
        """Endpoint to get collection from the backend using Bearer token in the header."""
        url = f"{self.base_url}/collection"
        token = await self._auth.get_token()
        headers = {
            "Authorization": f"Bearer {token}"  # Add the Bearer token in the headers
        }

        # Send GET request with the Bearer token
        response = self.session.get(url, headers=headers)

        # Check if the request was successful
        if response.status_code == 200:
            return response.json()  # Return the JSON response
        else:
            raise Exception(f"Failed to fetch collection: {response.status_code} {response.text}")