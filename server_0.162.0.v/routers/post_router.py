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
    posts = (db.query(Post).all())
    return {"posts": posts}

# get one propurti post
@router.get("/{id}")
def get_post_by_id(id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    post = db.query(Post).filter(Post.id == id, Post.user_id == current_user.id).first()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"post": post}
