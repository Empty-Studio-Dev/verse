from fastapi import FastAPI
from database.database import supabase

app = FastAPI()

@app.get("/health/db")
def health_db():
    try:
        res = supabase.table("test").select("*").limit(1).execute()
        return {"ok": True, "rows": len(res.data)}
    except Exception as e:
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}

# source .venv/bin/activate  
# uvicorn app.main:app --reload