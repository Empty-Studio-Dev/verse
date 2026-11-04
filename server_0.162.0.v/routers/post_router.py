from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from core import get_current_user
from models import Post, User
from database import get_db
from schemas import PostCreate, PostReplace, PostUpdate, PostOut

router = APIRouter(
    prefix="/posts",
    tags=["posts"],
)

# helpers
"""
    retrieves the post and 
    verifies that it belongs 
    to the current user
"""
def _get_owned_post(post_id: int, db: Session, current_user: User) -> Post:
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    if post.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this post",
        )
    return post



# CRUD
# basic method posts where user can CRUD

@router.get("", response_model=list[PostOut])
def get_all_posts(db: Session = Depends(get_db)):
    return db.query(Post).order_by(Post.created_at.desc(), Post.post_id.desc()).all()

# get one propurti post
@router.get("/{post_id}", response_model=PostOut)
def get_post_by_id(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post

@router.post("", response_model=PostOut, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = Post(**payload.model_dump(), user_id=current_user.user_id)
    db.add(post)
    db.commit()
    db.refresh(post)
    return post

@router.put("/{post_id}", response_model=PostOut)
def replace_post(post_id: int, payload: PostReplace, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = _get_owned_post(post_id, db, current_user)

    for field, value in payload.model_dump().items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post

@router.patch("/{post_id}", response_model=PostOut)
def update_post(post_id: int, payload: PostUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = _get_owned_post(post_id, db, current_user)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post = _get_owned_post(post_id, db, current_user)
    db.delete(post)
    db.commit()
    return None