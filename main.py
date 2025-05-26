from fastapi import FastAPI
from app.routers import authentication, facial_detections, roles, accounts, facial_detection_user_images
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles

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

@app.get("/")
async def just_test():
    return {
        "message": "Test Aivo Call is running.",
        "origin": origins
    }

app.include_router(authentication.router)
app.include_router(facial_detections.router)
app.include_router(roles.router)
app.include_router(accounts.router)
app.include_router(facial_detection_user_images.router)