import uvicorn
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse
from starlette.responses import FileResponse
from routes.parsing import router as  parsing
from fastapi import FastAPI, Request


templates = Jinja2Templates(directory="templates")



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