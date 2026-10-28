from fastapi import FastAPI
from database import Base, engine
from routers import user_router, auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

"""
TODO: 
 1) OAuth2 witch Google
 2) full Auth
 --------------------
 1) Need made pdf wraper for Json data where user open book
 2) AI assistend??? need check
 --------------------
 1) Need made store for picture 
"""

app.include_router(user_router.router)
app.include_router(auth_router.router)

# source .venv/bin/activate  
# uvicorn app.main:app --reload