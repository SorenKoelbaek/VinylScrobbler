import aiosqlite
import os
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from datetime import datetime, timedelta
import httpx
from config import settings
from dependencies.log_setup import get_logger

logger = get_logger(__name__)
DB_PATH = os.getenv("DB_PATH", "local_settings.db")

class AuthData(BaseModel):
    access_token: str
    refresh_token: str
    expires_at: datetime

class SettingsData(BaseModel):
    sound_input_device_name: str
    sound_output_device_name: str
    device_name: str
    listen_interval: int
    listen_length: int
    collection_first: bool


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS auth (
            id INTEGER PRIMARY KEY,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            expires_at TEXT NOT NULL
            );
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            sound_input_device_name   TEXT NOT NULL DEFAULT '',
            sound_output_device_name  TEXT NOT NULL DEFAULT '',
            device_name               TEXT NOT NULL,
            listen_interval           INTEGER NOT NULL,
            listen_length             INTEGER NOT NULL,
            collection_first          BOOLEAN NOT NULL
        );
        """)
        await db.commit()


async def save_auth(data: AuthData):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO auth (id, access_token, refresh_token, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                1,
                data.access_token,
                data.refresh_token,
                data.expires_at.isoformat(),
            ),
        )
        await db.commit()

async def save_settings(data: SettingsData):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT OR REPLACE INTO settings (
                id,
                sound_input_device_name,
                sound_output_device_name,
                device_name,
                listen_interval,
                listen_length,
                collection_first
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                1,
                data.sound_input_device_name,
                data.sound_output_device_name,
                data.device_name,
                data.listen_interval,
                data.listen_length,
                int(data.collection_first),
            ),
        )
        await db.commit()

async def get_auth() -> Optional[AuthData]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM auth WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if row:
                return AuthData(
                    access_token=row["access_token"],
                    refresh_token=row["refresh_token"],
                    expires_at=datetime.fromisoformat(row["expires_at"]),
                )
            return None

async def get_settings() -> Optional[SettingsData]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM settings WHERE id = 1") as cursor:
            row = await cursor.fetchone()
            if not row:
                return None
            return SettingsData(
                sound_input_device_name=row["sound_input_device_name"],
                sound_output_device_name=row["sound_output_device_name"],
                device_name=row["device_name"],
                listen_interval=row["listen_interval"],
                listen_length=row["listen_length"],
                collection_first=bool(row["collection_first"]),
            )


BACKEND_BASE_URL = settings.api_url
REFRESH_BUFFER = timedelta(minutes=5)

async def maybe_refresh_token() -> bool:
    auth = await get_auth()
    if not auth:
        return False  # Not logged in
    now = datetime.utcnow()
    if auth.expires_at - now > REFRESH_BUFFER:
        return True  # Token is still good

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_BASE_URL}/refresh-token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": auth.refresh_token,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.debug(f"🔴 Token refresh failed: {e}")
        return False

    await save_auth(AuthData(
        access_token=data["access_token"],
        refresh_token=data["refresh_token"],
        expires_at=datetime.fromisoformat(data["expires_at"])
    ))

    return True
