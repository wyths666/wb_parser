from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from wb_parser import WildberriesRobustParser
import time
router = APIRouter(prefix="/start", tags=["Pars"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def broadcast_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def start_parsing(request: Request):
    form_data = await request.form()
    text = form_data.get("text", "").strip()
    mode = form_data.get("mode", "").strip()
    parser = WildberriesRobustParser(headless=False)
    print("✅ Обработчик вызван!")
    print("text =", repr(text))
    print("mode =", repr(mode))
    message = ""
    success = False

    try:
        if mode == "search":
            keyword = text.strip()
            if not keyword:
                message = "❌ Ключевые слова не могут быть пустыми"
            else:
                products = parser.parse_by_keyword(keyword, max_products=50)
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
                products = parser.parse_by_seller(seller_id, max_products=50)
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

    # Возвращаем ту же страницу с сообщением
    return templates.TemplateResponse("index.html", {
        "request": request,
        "message": message,
        "success": success
    })

