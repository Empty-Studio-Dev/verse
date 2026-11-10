from fastapi import FastAPI
from database import Base, engine
from routers import user_router, auth_router, password_router, post_router, book_router, comment_router, like_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

"""
TODO: 
 1) OAuth2 witch Google
 --------------------
 1) Need made pdf wraper for Json data where user open book
 2) AI assistend??? need check
 --------------------
 1) Need made store for picture 
"""

app.include_router(user_router.router)
app.include_router(auth_router.router)
app.include_router(password_router.router)
app.include_router(post_router.router)
app.include_router(book_router.router)
app.include_router(comment_router.router)
app.include_router(like_router.router)


# source .venv/bin/activate  
# uvicorn app.main:app --reload