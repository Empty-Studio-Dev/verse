from fastapi import Depends, HTTPException, status, APIRouter
from sqlalchemy.orm import Session
from core import get_current_user
from models import Comment, User
from database import get_db
from schemas import CommentBase