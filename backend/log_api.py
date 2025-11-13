from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse
import os

router = APIRouter(prefix="/logs", tags=["Logs"])

LOG_PATH = os.path.join(os.path.dirname(__file__), "../startup.log")

@router.get("/startup", response_class=PlainTextResponse)
async def get_startup_log():
    """Return the content of startup.log as plain text (viewable in browser)."""
    if not os.path.exists(LOG_PATH):
        raise HTTPException(status_code=404, detail="Log file not found")

    try:
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return PlainTextResponse(content, media_type="text/plain; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")
