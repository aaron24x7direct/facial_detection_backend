from fastapi import APIRouter
from app.database.models import Role
from dotenv import load_dotenv
from pydantic import BaseModel
from starlette import status
from app.dependencies.db import db_dependency

load_dotenv()

router = APIRouter(
    prefix="/roles",
    tags=["roles"]
)

class CreateRoleRequest(BaseModel):
    name: str

@router.get("")
async def read_all_roles(db: db_dependency):
    roles = db.query(Role).all()
    return roles

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_role(db: db_dependency, create_role_request: CreateRoleRequest):
    create_role_model = Role(
        name=create_role_request.name
    )

    db.add(create_role_model)
    db.commit()