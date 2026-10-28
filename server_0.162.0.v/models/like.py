from sqlalchemy import Column, Integer, UniqueConstraint, CheckConstraint, func, ForeignKey
from sqlalchemy.orm import relationship
from datetime import date as py_date
from sqlalchemy import DateTime, func
from database import Base

class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="uq_like_user_post"),
        UniqueConstraint("user_id", "book_id", name="uq_like_user_book"),
        CheckConstraint("(post_id IS NULL) <> (book_id IS NULL)", name="ck_like_one_target"),
    )

    like_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    post_id = Column(Integer, ForeignKey("posts.post_id", ondelete="CASCADE"), nullable=True, index=True)
    book_id = Column(Integer, ForeignKey("books.book_id", ondelete="CASCADE"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="likes")
    post = relationship("Post", back_populates="likes")
    book = relationship("Book", back_populates="likes")
