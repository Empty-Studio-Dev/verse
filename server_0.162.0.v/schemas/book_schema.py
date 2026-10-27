from pydantic import BaseModel

class BookBase(BaseModel):
    title: str
    description: str
    cover_img_url: str
    bacground_img_url: str
    file: str