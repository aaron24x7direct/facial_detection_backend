from fastapi import FastAPI
from app.routers import authentication, facial_detections, roles, accounts, facial_detection_user_images
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from zoneinfo import ZoneInfo
import subprocess

load_dotenv()

origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/check-tesseract")
async def check_tesseract():
    try:
        # Run `tesseract --version` command
        result = subprocess.run(["tesseract", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            return {"tesseract_version": result.stdout.splitlines()[0]}
        else:
            return {"error": "Tesseract command failed", "details": result.stderr}
    except Exception as e:
        return {"error": str(e)}
    
@app.get("/")
async def just_test():
    return {
        "message": "Test Aivo Call is running.",
        "origin": origins,
        "date": datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Manila"))
    }

app.include_router(authentication.router)
app.include_router(facial_detections.router)
app.include_router(roles.router)
app.include_router(accounts.router)
app.include_router(facial_detection_user_images.router)