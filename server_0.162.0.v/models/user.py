from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import relationship
from database import Base



class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(26), nullable=False)
    email = Column(String(255), nullable=False, unique=True, index=True)
    password = Column(String(255), nullable=False)
    bio = Column(String(180), nullable=True)
    profile_img = Column(String, nullable=True)
    background_img = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    posts = relationship(
        "Post", back_populates="user",
        cascade="all, delete-orphan", passive_deletes=True,
    )
    comments = relationship("Comment", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan", passive_deletes=True)
    # added choice user and reset password
    reset_tokens = relationship("PasswordResetToken", back_populates="user", cascade="all, delete-orphan", passive_deletes=True,)
    