import requests
import json
import logging
from typing import Optional
from config import settings
from dependencies.database import get_auth, maybe_refresh_token

class Auth:
    _instance = None
    _token: Optional[str] = None

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(Auth, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.base_url = settings.api_url   # Change this to your FastAPI backend URL
        self.token = None
        self.expires = None

    async def auth(self) -> Optional[str]:
        """
        Authenticate using username and password and return the JWT token
        """
        await maybe_refresh_token()
        auth_data = await get_auth()
        if auth_data:
            self.token = auth_data.access_token
            logging.info(f"Using existing token: {self.token}")
            return self.token
        else:
            return None

    async def get_token(self) -> Optional[str]:
        """
        Get the token, if available
        """
        await maybe_refresh_token()
        auth_data = await get_auth()
        if auth_data:
            token = auth_data.access_token
            return token
        else:
            return None
        return await token

    async def is_authenticated(self) -> bool:
        """
        Check if the service is authenticated
        """
        token = await self.auth()
        return token is not None
