from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from database import Base


class Post(Base):
    __tablename__ = "posts"

    post_id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    description = Column(String(220), nullable=False)
    post_img = Column(ARRAY(String).with_variant(JSON, "sqlite"), nullable=True,)
    file = Column(String, nullable=True)
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")