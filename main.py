from fastapi import FastAPI
import uvicorn
from router import router, auth_router
from database import init_db

app = FastAPI(
    title="API Perencanaan Perjalanan",
    description="Implementasi API awal Desain Taktis Perencanaan Perjalanan",
    version="0.1.0"
)

# init database saat startup
@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(auth_router.router, prefix="/api/auth")
app.include_router(router.router, prefix="/api")

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Selamat datang di API Perencanaan Perjalanan"}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
