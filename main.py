import os
import urllib.request
import tarfile
from fastapi import FastAPI
from app.routers import authentication, facial_detections, roles, accounts, facial_detection_user_images
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

TESSERACT_DIR = "/tmp/tesseract"
TESSERACT_BIN = os.path.join(TESSERACT_DIR, "tesseract")

def download_tesseract():
    if not os.path.exists(TESSERACT_BIN):
        url = "https://github.com/tesseract-ocr/tesseract/releases/download/4.1.1/tesseract-ocr-linux-x86_64.tar.gz"
        archive_path = "/tmp/tesseract.tar.gz"
        urllib.request.urlretrieve(url, archive_path)
        with tarfile.open(archive_path, "r:gz") as tar:
            tar.extractall(path="/tmp")
        os.remove(archive_path)
    os.chmod(TESSERACT_BIN, 0o755)

def setup_pytesseract():
    import pytesseract
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_BIN

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

@app.on_event("startup")
async def startup_event():
    download_tesseract()
    setup_pytesseract()

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
