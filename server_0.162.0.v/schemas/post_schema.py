from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=220)
    post_img: list[str] | None = None
    file: str | None = None

class PostReplace(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=220)
    post_img: list[str] | None = None
    file: str | None = None

class PostUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=220)
    post_img: list[str] | None = None
    file: str | None = None

class PostOut(BaseModel):
    post_id: int
    title: str
    description: str
    post_img: list[str] | None = None
    file: str | None = None
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)