from core import get_current_user
from models import Post
from database import get_db
from schemas import PostBase, UpdatePostBase
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException, status, APIRouter

router = APIRouter(
    prefix="/posts"
)

# CRUD
# basic method posts where user can CRUD

@router.get("")
def get_all_posts(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    post = (db.query(Post).filter(Post.user_id == current_user.id).all())
    return {"posts": post}