from fastapi import Depends, HTTPException, status, APIRouter, Query
from sqlalchemy.orm import Session, joinedload

from core import get_current_user
from models import Comment, Post, User
from database import get_db
from schemas import CommentCreate, CommentOut

router = APIRouter(
    prefix="/posts",
    tags=["comments"],
)

# helper
def _ensure_post_exists(post_id: int, db: Session) -> Post:
    # if post not found
    post = db.query(Post).filter(Post.post_id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Post not found",
        )
    return post


@router.get("/{post_id}/comments", response_model=list[CommentOut])
def get_post_comments(post_id: int, db: Session = Depends(get_db), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    """
    all comment posts, old up.
    pagination: ?limit=50&offset=0
    """
    _ensure_post_exists(post_id, db)

    return db.query(Comment).options(joinedload(Comment.user)).filter(Comment.post_id == post_id).order_by(Comment.created_at.asc(), Comment.comment_id.asc()).offset(offset).limit(limit).all()


@router.post("/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def create_comment(post_id: int, payload: CommentCreate,db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _ensure_post_exists(post_id, db)

    comment = Comment(text_comment=payload.text_comment, post_id=post_id, user_id=current_user.user_id)
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment