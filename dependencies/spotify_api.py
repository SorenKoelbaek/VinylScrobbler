import httpx
from typing import Optional

class SpotifyAPI:
    def __init__(self, token: str):
        self.token = token
        self.base_url = "https://api.spotify.com/v1"

    async def get_track_info(self, track_id: str) -> Optional[dict]:
        url = f"{self.base_url}/tracks/{track_id}"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                return None

    async def get_current_playback(self) -> Optional[dict]:
        url = f"{self.base_url}/me/player"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 204:
                # No active device
                return None
            else:
                return None

