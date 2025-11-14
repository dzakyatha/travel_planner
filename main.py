from fastapi import FastAPI
import uvicorn
import router

app = FastAPI(
    title="API Perencanaan Perjalanan",
    description="Implementasi API awal Desain Taktis Perencanaan Perjalanan",
    version="0.1.0"
)

app.include_router(router.router, prefix="/api")

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Selamat datang di API Perencanaan Perjalanan"}

def main():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    main()
