import uvicorn
from routes.parsing import router as  parsing
from fastapi import FastAPI


app = FastAPI(title="WB Parser API")
app.include_router(parsing)


def start_server():
    """Запуск сервера"""
    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start_server()