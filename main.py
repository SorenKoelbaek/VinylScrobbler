# main.py
from datetime import timedelta, datetime
from system import main
import asyncio
from fastapi import FastAPI, HTTPException, Form
import httpx
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from dependencies.database import (
    init_db,
    get_settings,
    save_settings,
    get_auth,
    save_auth,
    SettingsData,
    AuthData,
)
from config import settings
import uvicorn
import sounddevice as sd
from fastapi.responses import JSONResponse
from dependencies.system_state import set_state, SystemStatus, state
system_task: asyncio.Task | None = None
from system import task_group  # Import the global TaskGroup
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
app.mount("/ui", StaticFiles(directory="static", html=True), name="static")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ⚠️ Dev only!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/system/status", response_class=JSONResponse)
async def system_status():
    return state
@app.get("/ui")
async def ui_redirect():
    auth = await get_auth()
    if auth:
        return RedirectResponse(url="/ui/main.html")
    return RedirectResponse(url="/ui/index.html")

def list_audio_devices() -> list[dict]:
    devices = sd.query_devices()
    return [
        {
            "name": dev["name"],
            "index": i,
            "max_input_channels": dev["max_input_channels"],
            "max_output_channels": dev["max_output_channels"]
        }
        for i, dev in enumerate(devices)
    ]


# SETTINGS
@app.get("/settings", response_model=SettingsData)
async def api_get_settings():
    settings = await get_settings()
    if not settings:
        raise HTTPException(status_code=404, detail="Settings not found")
    return settings


@app.post("/settings")
async def api_save_settings(settings: SettingsData):
    await save_settings(settings)
    return {"status": "ok"}


# AUTH
@app.get("/auth", response_model=AuthData)
async def api_get_auth():
    auth = await get_auth()
    if not auth:
        raise HTTPException(status_code=404, detail="Auth not found")
    return auth


@app.post("/auth/login")
async def login_through_backend(
    username: str = Form(...),
    password: str = Form(...)
):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.api_url}/token",  # <-- use your real URL
                data={"username": username, "password": password},
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()
            data = response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    except Exception:
        raise HTTPException(status_code=500, detail="Login failed")

    token = data["access_token"]
    refresh_token = data["refresh_token"]
    expires_at = datetime.utcnow() + timedelta(minutes=60)

    await save_auth(AuthData(
        access_token=token,
        refresh_token=refresh_token,
        expires_at=expires_at
    ))

    return {"status": "ok"}

@app.get("/sound-devices", response_class=JSONResponse)
async def get_sound_devices():
    devices = list_audio_devices()
    return devices


@app.post("/system/start")
async def start_system_manually():
    global system_task
    if system_task and not system_task.done():
        raise HTTPException(status_code=400, detail="System already running")

    settings = await get_settings()
    if not settings:
        raise HTTPException(status_code=400, detail="Missing settings")

    set_state(SystemStatus.RUNNING)
    system_task = asyncio.create_task(main())
    return {"status": "started"}

@app.post("/system/stop")
async def stop_system_manually():
    global system_task, task_group
    if not system_task:
        raise HTTPException(status_code=400, detail="System not running")

    if task_group:
        task_group.abort()
    system_task.cancel()

    try:
        await system_task
    except asyncio.CancelledError:
        pass

    set_state(SystemStatus.IDLE)
    return {"status": "stopped"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=6000, reload=True)


@app.on_event("startup")
async def start_system_on_boot():
    await init_db()
    global system_task
    settings = await get_settings()
    if settings:
        set_state(SystemStatus.RUNNING)
        system_task = asyncio.create_task(main())
    else:
        set_state(SystemStatus.IDLE)
        print("⚠️ No settings found — system will not start.")

@app.on_event("shutdown")
async def stop_system():
    global system_task
    if system_task:
        # TaskGroup abort should already have been called (e.g. from /system/stop)
        system_task.cancel()
        try:
            await system_task
        except asyncio.CancelledError:
            print("System task cancelled during shutdown.")
        finally:
            set_state(SystemStatus.IDLE)