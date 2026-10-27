from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=26)
    email: EmailStr
    password: str  = Field(min_length=8, max_length=72)

class UserOut(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class UpdateUserBase(BaseModel):
    name: str = Field(min_length=1, max_length=26)
    bio: str = Field(min_length=0, max_length=180)
    profile_img: str
    bacgroung_img: str