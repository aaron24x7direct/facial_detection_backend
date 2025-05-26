from typing import Annotated
from fastapi import Depends
from app.routers.authentication import get_current_user

user_dependency = Annotated[dict, Depends(get_current_user)]