from fastapi import APIRouter, HTTPException
from app.database.models import User, StudentInfo
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette import status
from app.dependencies.db import db_dependency
from app.dependencies.user import user_dependency
from app.routers.authentication import bcrypt_context
from sqlalchemy.orm import joinedload

load_dotenv()

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"]
)

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str

class ChangeAccountDetailsRequest(BaseModel):
    fullname: str
    email: str
    phone_number: int
    username: str

@router.get("/user", status_code=status.HTTP_200_OK)
async def user(db: db_dependency, user: user_dependency): 
    current_user = (
        db.query(User)
        .options(
            joinedload(User.role),
            joinedload(User.student_infos).joinedload(StudentInfo.subjects)
        )
        .filter(User.id == user["id"])
        .first()
    )
    return current_user

@router.put("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(db: db_dependency, user: user_dependency, change_password_request: ChangePasswordRequest):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")

    user_model = db.query(User).filter(User.id == user["id"]).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt_context.verify(change_password_request.old_password, user_model.password):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    if change_password_request.new_password != change_password_request.confirm_new_password:
        raise HTTPException(status_code=401, detail="New Password is not the same")

    user_model.password = bcrypt_context.hash(change_password_request.new_password)

    db.add(user_model)
    db.commit()

@router.put("/change-account-details", status_code=status.HTTP_201_CREATED)
async def change_account_details(db: db_dependency, user: user_dependency, change_account_details_request: ChangeAccountDetailsRequest):
    current_user_model = db.query(User).filter(User.id == user["id"]).first()
    
    if not current_user_model:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user.")

    current_user_model.fullname = change_account_details_request.fullname
    current_user_model.email = change_account_details_request.email
    current_user_model.phone_number = change_account_details_request.phone_number
    current_user_model.username = change_account_details_request.username

    db.add(current_user_model)
    db.commit()
