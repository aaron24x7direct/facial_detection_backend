from datetime import timedelta, datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from starlette import status
from app.database.models import User
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
from fastapi.responses import JSONResponse
import traceback
from app.dependencies.db import db_dependency

router = APIRouter(
    prefix="/authenticated",
    tags=["authenticated"]
)

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
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user

def create_access_token(email: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": email, "id": user_id}
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

    token = create_access_token(users.email, users.id, timedelta(minutes=500))

    return {"access_token": token, "token_type": "bearer"}

