from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from core import get_current_user
from models import Book
from database import get_db
from schemas import BookBase

router = APIRouter(
    prefix="/books",
    tags=["books"],
)

@router.get("", response_model=list[BookBase])
def get_all_books(db: Session = Depends(get_db)):
    return db.query(Book).order_by(Book.created_at.desc(), Book.book_id.desc()).all()

@router.get("/{book_id}", response_model=BookBase)
def get_book_by_id(book_id: int, db: Session = Depends(get_db)):
    book = db.query(Book).filter(Book.book_id == book_id).filter()
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found",
        )
    return book