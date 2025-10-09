from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from fastapi.responses import FileResponse
import os
from wb_parser import WildberriesRobustParser
import time
import urllib.parse

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def broadcast_page(request: Request, message: str = None, success: bool = None, filename: str = None):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "success": success,
        "filename": filename
    })


@router.post("/", response_class=HTMLResponse)
async def start_parsing(request: Request):
    form_data = await request.form()
    text = form_data.get("text", "").strip()
    mode = form_data.get("mode", "").strip()
    qty = form_data.get("qty", "").strip()
    qty = int(qty)
    parser = WildberriesRobustParser(headless=True)

    print("✅ Обработчик вызван!")
    print("text =", repr(text))
    print("mode =", repr(mode))
    print("qty =", repr(qty))

    message = ""
    success = False
    filename = None

    try:
        if mode == "search":
            keyword = text.strip()
            if not keyword:
                message = "❌ Ключевые слова не могут быть пустыми"
            else:
                products = parser.parse_by_keyword(keyword, qty)
                if products:
                    filename = f"wildberries_{keyword.replace(' ', '_')}_{int(time.time())}.xlsx"
                    parser.save_to_excel(products, filename)
                    message = f"✅ Парсинг завершён! Сохранено {len(products)} товаров в файл: {filename}"
                    success = True
                else:
                    message = "❌ Не удалось найти товары по вашему запросу"

        elif mode == "seller":
            seller_id = text.strip()
            if not seller_id:
                message = "❌ ID продавца не может быть пустым"
            else:
                products = parser.parse_by_seller(seller_id, qty)
                if products:
                    filename = f"wildberries_seller_{seller_id}_{int(time.time())}.xlsx"
                    parser.save_to_excel(products, filename)
                    message = f"✅ Парсинг завершён! Сохранено {len(products)} товаров продавца {seller_id}"
                    success = True
                else:
                    message = "❌ Не удалось найти товары для этого продавца"
        else:
            message = "❌ Неизвестный режим парсинга"

    except Exception as e:
        message = f"❌ Ошибка при парсинге: {str(e)}"
        success = False
        filename = None

    finally:
        parser.close()

    # Подготовим параметры для редиректа
    params = []
    if message:
        params.append(f"message={urllib.parse.quote(message)}")
    if success is not None:
        params.append(f"success={1 if success else 0}")
    if filename:
        params.append(f"filename={urllib.parse.quote(filename)}")

    query_string = "&".join(params)
    redirect_url = f"/?{query_string}"

    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/download/{filename}")
async def download_file(filename: str):
    # Защита от path traversal
    if ".." in filename or filename.startswith("/"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Недопустимое имя файла")

    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Файл не найден")