from fastapi import Depends, HTTPException, status, APIRouter, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core import get_current_user
from models import Like, Post, Book, User
from database import get_db
from schemas import PostOut, LikeToggleOut

router = APIRouter(tags=["likes"])

# helpers
def _count_likes(db: Session, **target) -> int:
    """target — {'post_id': 5}, or {'book_id': 3}."""
    return db.query(Like).filter_by(**target).count()


def _toggle(db: Session, user_id: int, **target) -> LikeToggleOut:
    like = db.query(Like).filter(
        Like.user_id == user_id,
        *[getattr(Like, k) == v for k, v in target.items()],
    ).first()

    if like:
        db.delete(like)
        db.commit()
        return LikeToggleOut(liked=False, likes_count=_count_likes(db, **target))

    db.add(Like(user_id=user_id, **target))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return LikeToggleOut(liked=True, likes_count=_count_likes(db, **target))

    return LikeToggleOut(liked=True, likes_count=_count_likes(db, **target))

# rest
@router.post("/posts/{post_id}/like", response_model=LikeToggleOut)
def toggle_post_like(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Post).filter(Post.post_id == post_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    return _toggle(db, current_user.user_id, post_id=post_id)


@router.get("/posts/{post_id}/like", response_model=LikeToggleOut)
def get_post_like_status(post_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Post).filter(Post.post_id == post_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    liked = db.query(Like).filter(Like.user_id == current_user.user_id, Like.post_id == post_id,).first() is not None

    return LikeToggleOut(liked=liked,
                         likes_count=_count_likes(db, post_id=post_id))

@router.post("/books/{book_id}/like", response_model=LikeToggleOut)
def toggle_book_like(book_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not db.query(Book).filter(Book.book_id == book_id).first():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Book not found")

    return _toggle(db, current_user.user_id, book_id=book_id)

@router.get("/users/me/likes/posts", response_model=list[PostOut])
def get_my_liked_posts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    return (
        db.query(Post)
        .join(Like, Like.post_id == Post.post_id)
        .filter(Like.user_id == current_user.user_id)
        .order_by(Like.created_at.desc(), Like.like_id.desc())
        .offset(offset).limit(limit)
        .all()
    )


@router.get("/users/me/likes/books")
def get_my_liked_books(db: Session = Depends(get_db), current_user: User = Depends(get_current_user), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    return (
        db.query(Book)
        .join(Like, Like.book_id == Book.book_id)
        .filter(Like.user_id == current_user.user_id)
        .order_by(Like.created_at.desc(), Like.like_id.desc())
        .offset(offset).limit(limit)
        .all()
    )