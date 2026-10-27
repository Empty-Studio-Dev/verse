from models import User
from fastapi import Depends, HTTPException, status, APIRouter
from database import get_db
from schemas import CreateUser, UserOut
from sqlalchemy.orm import Session