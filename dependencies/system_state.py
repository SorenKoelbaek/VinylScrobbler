# system_state.py
from enum import Enum
from typing import Optional
import datetime

class SystemStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    ERROR = "error"

state = {
    "status": SystemStatus.IDLE,
    "last_updated": None,
    "last_error": None
}

def set_state(status: SystemStatus, error: Optional[str] = None):
    state["status"] = status
    state["last_updated"] = datetime.datetime.utcnow().isoformat()
    state["last_error"] = error

