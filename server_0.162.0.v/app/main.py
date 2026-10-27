from fastapi import FastAPI
from database import Base, engine
from models import User, Post, Like, Comment, Book

Base.metadata.create_all(bind=engine)

app = FastAPI()



# source .venv/bin/activate  
# uvicorn app.main:app --reload