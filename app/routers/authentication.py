from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from starlette import status
from app.database.models import User, Subject, StudentInfo
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.responses import JSONResponse
import traceback
from app.dependencies.db import db_dependency
from sqlalchemy.orm import joinedload
import os
from uuid import uuid4
from pathlib import Path
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
import re
from sqlalchemy.exc import IntegrityError

router = APIRouter(
    prefix="/authenticated",
    tags=["authenticated"]
)

UPLOAD_DIR = Path("static/uploads/authentication")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = "ebaf820937a47bc5e51b0cfadbc2ff85ce0bd35fa2ad2ab8241a9e4bbc454dc2"
ALGORITHM = "HS256"

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='authenticated/token')

class CreateNameRequest(BaseModel):
    name: str

class CreateUserRequest(BaseModel):
    role_id: int
    fullname: str
    section: str
    username: str
    email: str
    phone_number: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


def authenticate_user(email: str, password: str, db):
    user = db.query(User).options(joinedload(User.role)).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(email: str, user_id: int, section: str, fullname: str, role: str, expires_delta: timedelta):
    encode = {"sub": email, "id": user_id, "section": section, "fullname": fullname, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get('sub')
        user_id: int = payload.get('id')
        if email is None or user_id is None:
            HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")
        return {"email": email, "id": user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

@router.get("/users", status_code=status.HTTP_200_OK)
async def users(db: db_dependency):
    try:
        return db.query(User).all()
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": f"An error occurred: {str(e)}"}
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    create_user_model = User(
        role_id=create_user_request.role_id,
        fullname=create_user_request.fullname,
        section=create_user_request.section,
        username=create_user_request.username,
        email=create_user_request.email,
        phone_number=create_user_request.phone_number,
        is_email_verified=False,
        password=bcrypt_context.hash(create_user_request.password),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency):
    users = authenticate_user(form_data.username, form_data.password, db)
    if not users:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

    token = create_access_token(users.email, users.id, users.section, users.fullname, users.role.name, timedelta(minutes=500))

    return {"access_token": token, "token_type": "bearer"}

@router.post("/upload-pdf", status_code=status.HTTP_201_CREATED)
async def upload_pdf_ocr(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

    file_name = f"{uuid4().hex}.pdf"
    file_path = UPLOAD_DIR / file_name

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        images = convert_from_path(str(file_path), dpi=300)
    except Exception as e:
        return {"error": f"Failed to convert PDF to images: {e}"}

    extracted_text = ""
    try:
        for i, image in enumerate(images):
            page_text = pytesseract.image_to_string(image)
            extracted_text += f"\n--- Page {i+1} ---\n{page_text}"
    except Exception as e:
        return {"error": f"OCR failed: {e}"}

    text = extracted_text.replace("\n", " ")
    text = re.sub(r"__\s*:\s*", ": ", text)
    text = re.sub(r"[_]{2,}", "", text)

    def extract_field(label, stop_labels=None):
        pattern = rf"{label}\s*[:_]*\s*(.*?)($|"
        if stop_labels:
            pattern += "|".join([re.escape(lbl) for lbl in stop_labels])
        pattern += ")"
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else None

    campus_match = re.search(r"Campus\s*(?:__\s*:|:)?\s*(.*?)\s+Academic Term", text, re.IGNORECASE)
    campus = campus_match.group(1).strip() if campus_match else None

    fields = {
        "Campus": campus,
        "Academic Term": extract_field("Academic Term", ["Academic Year"]),
        "Academic Year": extract_field("Academic Year", ["Student Number"]),
        "Student Number": extract_field("Student Number", ["LRN"]),
        "LRN": extract_field("LRN", ["Year/Status"]),
        "Year/Status": extract_field("Year/Status", ["Full Name"]),
        "Full Name": extract_field("Full Name", ["Sex"]),
        "Sex": extract_field("Sex", ["Course"]),
        "Course": extract_field("Course", ["Major"]),
        "Major": extract_field("Major", ["Contact #"]),
        "Contact #": extract_field("Contact #", ["Home Address"]),
        "Home Address": extract_field("Home Address")
    }

    subjects_text = ""
    subjects_header_match = re.search(r"Subject/s Section Lab Units Lec Units Days Time.*?Room", extracted_text, re.IGNORECASE)
    if subjects_header_match:
        start_pos = subjects_header_match.end()
        end_match = re.search(r"Tuition Fee|Other Fees|Total Amount", extracted_text[start_pos:], re.IGNORECASE)
        end_pos = start_pos + end_match.start() if end_match else len(extracted_text)
        subjects_text = extracted_text[start_pos:end_pos].strip()

    subjects = []
    for line in subjects_text.split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split()

        if len(parts) < 7:
            continue

        subject_code = parts[0]
        section = parts[1]
        try:
            lab_units = int(parts[2])
            lec_units = int(parts[3])
        except ValueError:
            continue
        days = parts[4].upper()

        if '-' in parts:
            dash_index = parts.index('-')
            time_start = " ".join(parts[5:dash_index])
            time_end = " ".join(parts[dash_index+1:dash_index+3])
            time = f"{time_start} - {time_end}"
            room = " ".join(parts[dash_index+3:]) if len(parts) > dash_index + 3 else ""
        else:
            time = " ".join(parts[5:7])
            room = " ".join(parts[7:]) if len(parts) > 7 else ""

        subjects.append({
            "Subject Code": subject_code,
            "Section": section,
            "Lab Units": lab_units,
            "Lec Units": lec_units,
            "Days": days,
            "Time": time,
            "Room": room
        })

    if None in fields.values():
        return {
            "error": "Failed to extract all required fields accurately",
            "fields": fields
        }

    return {
        "filename": file_name,
        "fields": fields,
        "subjects": subjects,
        "extracted_text": extracted_text.strip()
    }

class SubjectCreate(BaseModel):
    subject_code: str
    section: str
    lec_units: int
    lab_units: int
    days: str
    time: str
    room: str


class StudentInfoCreate(BaseModel):
    fullname: str
    student_number: str
    lrn: str
    sex: str
    course: str
    major: Optional[str] = None
    year_status: str
    academic_term: str
    academic_year: str
    campus: str
    contact: str
    home_address: Optional[str] = None


class UserCreateWithORF(BaseModel):
    email: EmailStr
    password: str
    student_infos: StudentInfoCreate
    subjects: List[SubjectCreate]

@router.post("/create-account-with-orf")
async def create_account_with_orf(user_data: UserCreateWithORF, db: db_dependency):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        # Create User
        user = User(
            role_id= 1,
            email=user_data.email,
            password=bcrypt_context.hash(user_data.password),
            username=user_data.email.split('@')[0],
            fullname=user_data.student_infos.fullname,
            phone_number=user_data.student_infos.contact,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create StudentInfo
        student_info = StudentInfo(
            user_id=user.id,
            campus=user_data.student_infos.campus,
            academic_term=user_data.student_infos.academic_term,
            academic_year=user_data.student_infos.academic_year,
            student_number=user_data.student_infos.student_number,
            lrn=user_data.student_infos.lrn,
            year_status=user_data.student_infos.year_status,
            fullname=user_data.student_infos.fullname,
            sex=user_data.student_infos.sex,
            course=user_data.student_infos.course,
            contact=user_data.student_infos.contact,
        )
        db.add(student_info)
        db.commit()
        db.refresh(student_info)

        # Create Subjects
        for subj in user_data.subjects:
            subject = Subject(
                student_info_id=student_info.id,
                subject_code=subj.subject_code,
                section=subj.section,
                lec_units=subj.lec_units,
                lab_units=subj.lab_units,
                days=subj.days,
                time=subj.time,
                room=subj.room
            )
            db.add(subject)

        db.commit()

        return {"message": "Account created successfully", "user_id": user.id}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database integrity error")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    db: db_dependency,
    user_id: int = Path(gt=0)
):
    user = db.query(User).filter(User.id == user_id).first()

    db.delete(user)
    db.commit()
