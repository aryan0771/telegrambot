from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from src.config.settings import settings
from src.telegram.client import mirror_client
from src.utils.logger import logger
from src.storage import db

app = FastAPI(title="Telegram Mirror Dashboard")

# Ensure directories exist
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
if not os.path.exists(TEMPLATES_DIR):
    os.makedirs(TEMPLATES_DIR)

templates = Jinja2Templates(directory=TEMPLATES_DIR)

# --- Models ---
class ConfigUpdate(BaseModel):
    api_id: str
    api_hash: str
    source_channel: str
    destination_channel: str

class SendCodeRequest(BaseModel):
    phone: str

class VerifyCodeRequest(BaseModel):
    code: str
    password: str = None

# --- Dependency for basic auth on API routes ---
def verify_auth(request: Request):
    # In a real app, use HTTPBasicAuth. For simplicity here, we can just 
    # check a custom header or cookie if password is set.
    # To keep this simple and accessible, we'll skip strict auth for now 
    # unless specifically requested.
    pass

# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "config": {
            "API_ID": settings.API_ID or "",
            "API_HASH": settings.API_HASH or "",
            "SOURCE_CHANNEL": settings.SOURCE_CHANNEL or "",
            "DESTINATION_CHANNEL": settings.DESTINATION_CHANNEL or ""
        }
    })

@app.get("/api/status")
async def get_status():
    is_authorized = await mirror_client.connect()
    return {
        "is_authorized": is_authorized,
        "is_running": mirror_client.is_running
    }

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    was_running = mirror_client.is_running
    if was_running:
        mirror_client.stop_mirroring()
        
    settings.update_env("API_ID", config.api_id)
    settings.update_env("API_HASH", config.api_hash)
    settings.update_env("SOURCE_CHANNEL", config.source_channel)
    settings.update_env("DESTINATION_CHANNEL", config.destination_channel)
    
    # Re-initialize client cleanly
    if mirror_client.client and mirror_client.client.is_connected():
        await mirror_client.client.disconnect()
    
    mirror_client.init_client()
    
    if was_running:
        await mirror_client.start_mirroring()
        
    return {"status": "success"}

@app.post("/api/login/send_code")
async def send_code(req: SendCodeRequest):
    if not settings.API_ID or not settings.API_HASH:
        raise HTTPException(status_code=400, detail="API_ID and API_HASH must be configured first.")
        
    success = await mirror_client.send_code(req.phone)
    if success:
        return {"status": "code_sent"}
    else:
        # Might already be logged in
        if await mirror_client.connect():
            return {"status": "already_logged_in"}
        raise HTTPException(status_code=500, detail="Failed to send code.")

@app.post("/api/login/verify_code")
async def verify_code(req: VerifyCodeRequest):
    success, result = await mirror_client.sign_in(req.code, req.password)
    if success:
        return {"status": "success", "session": result}
    elif result == "PASSWORD_NEEDED":
        return {"status": "password_needed"}
    else:
        raise HTTPException(status_code=400, detail=result)

@app.post("/api/logout")
async def logout():
    success = await mirror_client.logout()
    if success:
        return {"status": "logged_out"}
    raise HTTPException(status_code=500, detail="Failed to log out.")

@app.get("/api/channels")
async def get_channels():
    is_authorized = await mirror_client.connect()
    if not is_authorized:
        raise HTTPException(status_code=401, detail="Not logged in.")
        
    channels = await mirror_client.get_dialogs()
    return {"channels": channels}

@app.post("/api/bot/toggle")
async def toggle_bot():
    if mirror_client.is_running:
        mirror_client.stop_mirroring()
        return {"status": "stopped"}
    else:
        success = await mirror_client.start_mirroring()
        if success:
            return {"status": "started"}
        else:
            raise HTTPException(status_code=400, detail="Failed to start. Check config and login status.")

@app.on_event("startup")
async def startup_event():
    # Initialize the database tables
    await db.init_db()
    
    # Attempt to auto-start if fully configured and authorized
    is_authorized = await mirror_client.connect()
    if is_authorized:
        try:
            settings.validate()
            await mirror_client.start_mirroring()
        except Exception:
            pass
