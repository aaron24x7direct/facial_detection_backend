from fastapi import APIRouter, HTTPException
from app.database.models import FacialDetection, User, StudentInfo, Subject
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from starlette import status
from app.dependencies.db import db_dependency
from app.dependencies.user import user_dependency
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime, timedelta, time
from collections import defaultdict

load_dotenv()

router = APIRouter(
    prefix="/facial_detections",
    tags=["facial_detections"]
)

class FacialDetectionRequest(BaseModel):
    user_id: int

@router.get("/graph/me", status_code=status.HTTP_200_OK)
async def get_facial_detection_graph(db: db_dependency, user: user_dependency):
    results = (
        db.query(
            func.date(FacialDetection.created_at).label("date"),
            func.count(FacialDetection.id).label("count")
        )
        .filter(FacialDetection.user_id == user["id"])
        .group_by(func.date(FacialDetection.created_at))
        .order_by(func.date(FacialDetection.created_at))
        .all()
    )

    return [{"date": date.strftime("%Y-%m-%d"), "count": count} for date, count in results]

@router.get("/graph", status_code=status.HTTP_200_OK)
async def get_facial_detection_graph(db: db_dependency):
    results = (
        db.query(
            func.date(FacialDetection.created_at).label("date"),
            func.count(FacialDetection.id).label("count")
        )
        .group_by(func.date(FacialDetection.created_at))
        .order_by(func.date(FacialDetection.created_at))
        .all()
    )

    return [{"date": date.strftime("%Y-%m-%d"), "count": count} for date, count in results]

@router.get("", status_code=status.HTTP_200_OK)
async def read_all_facial_detection(db: db_dependency):
    facial_detections = db.query(FacialDetection).options(joinedload(FacialDetection.user)).options(joinedload(FacialDetection.subject)).all()
    return facial_detections

@router.get("/me", status_code=status.HTTP_200_OK)
async def my_facial_detection(db: db_dependency, user: user_dependency):
    facial_detections = db.query(FacialDetection).options(joinedload(FacialDetection.user)).options(joinedload(FacialDetection.subject)).filter(FacialDetection.user_id == user["id"]).all()
    return facial_detections

@router.get("/section", status_code=status.HTTP_200_OK)
async def section_facial_detection(db: db_dependency, user: user_dependency):
    current_user = db.query(User).options(joinedload(User.professor_infos)).filter(User.id == user["id"]).first()

    sections = [info.section for info in current_user.professor_infos]
    subjects = [info.subject for info in current_user.professor_infos]

    facial_detections = db.query(FacialDetection)\
        .options(joinedload(FacialDetection.user))\
        .options(joinedload(FacialDetection.subject))\
        .filter(FacialDetection.subject.has(Subject.section.in_(sections)))\
        .filter(FacialDetection.subject.has(Subject.subject_code.in_(subjects)))\
        .all()

    grouped_data = defaultdict(lambda: defaultdict(list))

    for detection in facial_detections:
        section = detection.subject.section
        subject_code = detection.subject.subject_code
        grouped_data[section][subject_code].append(detection)

    # Optional: Convert defaultdicts to regular dicts for FastAPI to return clean JSON
    result = {
        section: {
            subject: detections
            for subject, detections in subjects_dict.items()
        }
        for section, subjects_dict in grouped_data.items()
    }

    return result

def parse_time_range(time_range: str):
    try:
        start_str, end_str = time_range.split("-")
        start_time = datetime.strptime(start_str.strip(), "%I:%M %p").time()
        end_time = datetime.strptime(end_str.strip(), "%I:%M %p").time()
        return start_time, end_time
    except Exception:
        return None, None

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_facial_detection(db: db_dependency, facial_detection_request: FacialDetectionRequest):
    user = db.query(User).options(
        joinedload(User.role),
        joinedload(User.student_infos).joinedload(StudentInfo.subjects)
    ).filter(User.id == facial_detection_request.user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    now = datetime.now()
    current_day = now.strftime("%A")[0].upper()  # e.g., 'M', 'T', etc.
    current_time = now.time()

    matched_subject = None
    attendance_status = None

    for info in user.student_infos:
        for subject in info.subjects:
            if current_day not in subject.days:
                continue

            start_time, end_time = parse_time_range(subject.time)
            if not start_time or not end_time:
                continue

            early_window = (datetime.combine(now.date(), start_time) - timedelta(minutes=10)).time()

            # present if within 10 minutes before start_time until start_time
            if early_window <= current_time < start_time:
                matched_subject = subject
                attendance_status = "Present"
                break
            # late if between start_time and end_time
            elif start_time <= current_time <= end_time:
                matched_subject = subject
                attendance_status = "Late"
                break

        if matched_subject:
            break

    if not matched_subject or not attendance_status:
        raise HTTPException(status_code=400, detail="You are not within the valid time window for facial detection")

    # Check if detection already exists today
    today_start = datetime.combine(now.date(), time.min)
    today_end = datetime.combine(now.date(), time.max)

    existing_detection = db.query(FacialDetection).filter(
        FacialDetection.user_id == user.id,
        FacialDetection.subject_id == matched_subject.id,
        FacialDetection.created_at >= today_start,
        FacialDetection.created_at <= today_end
    ).first()

    if existing_detection:
        raise HTTPException(status_code=400, detail="Facial detection already recorded for this subject today")

    facial_detection_model = FacialDetection(
        user_id=user.id,
        subject_id=matched_subject.id,
        status=attendance_status
    )

    db.add(facial_detection_model)
    db.commit()

    return {"message": "Facial detection recorded successfully", "status": attendance_status}