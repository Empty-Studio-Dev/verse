from pydantic import BaseModel, Field

class CommentBase(BaseModel):
    text_comment: str = Field(min_length=1, max_length=280)
