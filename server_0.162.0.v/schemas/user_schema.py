import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from utils import password_regex

class CreateUser(BaseModel):
    name: str = Field(min_length=1, max_length=26)
    email: EmailStr
    password: str  = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError(
                "The password must be no more than 72 characters long!"
            )
        if re.fullmatch(password_regex, value) is None:
            raise ValueError(
                "The password must contain a lowercase Latin letter, "
                "an uppercase Latin letter, a digit, and a special character!"
            )
        return value

class UserOut(BaseModel):
    user_id: int
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
    bio: str | None = Field(default=None, max_length=180)
    profile_img: str | None = None
    bacgroung_img: str | None = None