from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from app.database.models import FacialDetectionUserImage
from dotenv import load_dotenv
from starlette import status
from app.dependencies.db import db_dependency
from app.dependencies.user import user_dependency
import os
from uuid import uuid4
from pathlib import Path
from sqlalchemy.orm import joinedload

load_dotenv()

router = APIRouter(
    prefix="/facial_detection_user_images",
    tags=["facial_detection_user_images"]
)

UPLOAD_DIR = Path("static/uploads/facial_detection_user_images")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/datasets")
async def datasets_facial_detection_user_images(
    db: db_dependency
):
    datasets = db.query(FacialDetectionUserImage).options(joinedload(FacialDetectionUserImage.user)).all()
    return datasets

@router.get("")
async def read_all_facial_detection_user_images(
    db: db_dependency, 
    user: user_dependency
):
    facial_detection_user_images = db.query(FacialDetectionUserImage).filter(FacialDetectionUserImage.user_id == user['id']).all()
    return facial_detection_user_images

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_facial_detection_user_images(
    db: db_dependency,
    user: user_dependency,
    image_1: UploadFile = File(None),
    image_2: UploadFile = File(None),
    image_3: UploadFile = File(None),
    image_4: UploadFile = File(None),
    image_5: UploadFile = File(None),
):
    uploaded_files = [image_1, image_2, image_3, image_4, image_5]
    saved_images = []

    for file in uploaded_files:
        if file:
            ext = os.path.splitext(file.filename)[-1]
            file_name = f"{uuid4().hex}{ext}"
            file_path = UPLOAD_DIR / file_name

            with open(file_path, "wb") as buffer:
                buffer.write(await file.read())

            image_model = FacialDetectionUserImage(
                user_id=user["id"],
                image_path=str(file_path),
            )
            db.add(image_model)
            saved_images.append(image_model)

    db.commit()
    for image_model in saved_images:
        db.refresh(image_model)

    return saved_images

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def create_facial_detection_user_image(
    db: db_dependency,
    user: user_dependency,
    image: UploadFile = File(...),
):
    ext = os.path.splitext(image.filename)[-1]
    file_name = f"{uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / file_name

    with open(file_path, "wb") as buffer:
        buffer.write(await image.read())

    image_model = FacialDetectionUserImage(
        user_id=user["id"],
        image_path=str(file_path),
    )
    db.add(image_model)
    db.commit()
    db.refresh(image_model)

    return image_model

@router.delete("/{facial_detection_user_image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_facial_detection_user_image(
    db: db_dependency,
    user: user_dependency,
    facial_detection_user_image_id: int = Path(gt=0)
):
    image = db.query(FacialDetectionUserImage).filter_by(
        id=facial_detection_user_image_id,
        user_id=user["id"]
    ).first()

    if not image:
        raise HTTPException(status_code=404, detail="Image not found.")

    try:
        if os.path.exists(image.image_path):
            os.remove(image.image_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting image file: {str(e)}")

    db.delete(image)
    db.commit()

    return
