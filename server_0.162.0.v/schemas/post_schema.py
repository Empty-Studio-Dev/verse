from pydantic import BaseModel, Field
from datetime import date

class PostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=220) 

class UpdatePostBase(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=220) 
    post_img: list[str] | None = None
    file: str | None = None