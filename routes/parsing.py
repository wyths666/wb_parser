from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from fastapi.responses import FileResponse
import os
from wb_parser import WildberriesRobustParser
import time
router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/")
async def broadcast_page(request: Request, message: str = None, success: bool = None):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "success": success
    })

@router.post("/", response_class=HTMLResponse)
async def start_parsing(request: Request):
    form_data = await request.form()
    text = form_data.get("text", "").strip()
    mode = form_data.get("mode", "").strip()
    qty = form_data.get("qty", "".strip())
    qty = int(qty)
    parser = WildberriesRobustParser(headless=True)
    print("✅ Обработчик вызван!")
    print("text =", repr(text))
    print("mode =", repr(mode))
    print("qty =", repr(qty))
    message = ""
    success = False

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
    finally:
        parser.close()

    return RedirectResponse(
        url=f"/?message={message}&success={success}",
        status_code=303
    )



@router.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(os.getcwd(), filename)  # или укажите путь явно
    if os.path.exists(file_path):
        return FileResponse(path=file_path, filename=filename)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Файл не найден")