from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

class CommentBase(BaseModel):
    text_comment: str = Field(min_length=1, max_length=280)

class CommentCreate(CommentBase):
    pass

class CommentAuthor(BaseModel):
    user_id: int
    name: str
    profile_img: str | None = None

    model_config = ConfigDict(from_attributes=True)

class CommentOut(BaseModel):
    comment_id: int
    text_comment: str
    user_id: int
    post_id: int
    created_at: datetime
    user: CommentAuthor | None = None 

    model_config = ConfigDict(from_attributes=True)