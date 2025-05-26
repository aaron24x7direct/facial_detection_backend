from fastapi import APIRouter
from app.database.models import FacialDetection
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from starlette import status
from app.dependencies.db import db_dependency
from app.dependencies.user import user_dependency

load_dotenv()

router = APIRouter(
    prefix="/facial_detections",
    tags=["facial_detections"]
)

class FacialDetectionRequest(BaseModel):
    fullname: str = Field(min_length=3)


@router.get("", status_code=status.HTTP_200_OK)
async def read_all_facial_detection(db: db_dependency):
    facial_detections = db.query(FacialDetection).all()
    return facial_detections

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_facial_detection(db: db_dependency, facial_detection_request: FacialDetectionRequest):
    facial_detection_model = FacialDetection(**facial_detection_request.model_dump())

    db.add(facial_detection_model)
    db.commit()