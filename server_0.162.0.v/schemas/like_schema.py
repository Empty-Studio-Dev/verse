from pydantic import BaseModel

class LikeToggleOut(BaseModel):
    liked: bool
    likes_count: int