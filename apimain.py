from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from routes.parsing import router as  parsing
from fastapi import FastAPI, Request


templates = Jinja2Templates(directory="templates")



app = FastAPI(title="WB Parser API")
@app.get("/test")
async def test_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/test")
async def test_post(request: Request):
    print("✅ ТЕСТОВЫЙ ЭНДПОИНТ ВЫЗВАН!")
    form_data = await request.form()
    text = form_data.get("text", "")
    mode = form_data.get("mode", "")
    print(f"text: {text}, mode: {mode}")
    return {"status": "ok", "text": text, "mode": mode}

@app.get("/")
async def root():
    return {"message": "Go to /start/"}


@app.middleware("http")
async def log_requests(request: Request, call_next):
    if request.method == "POST" and "/start/" in str(request.url):
        body = await request.body()
        print("🔍 RAW BODY:", body)
        form = await request.form()
        print("🔍 PARSED FORM:", dict(form))
    response = await call_next(request)
    return response
#
# print("✅ Роуты до подключения:", list(app.routes))
app.include_router(parsing)
# print("✅ Роуты после подключения:", list(app.routes))


#uvicorn apimain:app --reload