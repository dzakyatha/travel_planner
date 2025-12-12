from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from router.router import router
from router.auth_router import router as auth_router
from database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # initialize database
    init_db()
    yield
    # shutdown
    pass

app = FastAPI(
    title="API Perencanaan Perjalanan",
    description="Implementasi API awal Desain Taktis Perencanaan Perjalanan",
    version="0.1.0",
    lifespan=lifespan
)

app.include_router(auth_router, prefix="/api/auth")
app.include_router(router, prefix="/api")

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Selamat datang di API Perencanaan Perjalanan"}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
