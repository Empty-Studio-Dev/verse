import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from utils import password_regex

def _validate_password(value: str) -> str:
    if len(value.encode("utf-8")) > 72:
        raise ValueError("The password must be no more than 72 characters long!")
    if re.fullmatch(password_regex, value) is None:
        raise ValueError(
            "The password must contain a lowercase Latin letter, "
            "an uppercase Latin letter, a digit, and a special character!"
        )
    return value

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        return _validate_password(v)