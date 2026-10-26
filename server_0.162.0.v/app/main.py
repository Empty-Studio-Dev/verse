from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello, FastAPI"}

# source .venv/bin/activate  
# uvicorn app.main:app --reload