from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import pandas as pd
import time
import re
from urllib.parse import quote

from redactor import redact


class WildberriesRobustParser:
    def __init__(self, headless=True):
        self.driver = None
        self.setup_driver(headless)

    def setup_driver(self, headless=True):
        """Настройка веб-драйвера"""
        print("Запуск браузера...")
        chrome_options = Options()

        if headless:
            chrome_options.add_argument('--headless')

        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_argument('--window-size=1920,1080')

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        self.wait = WebDriverWait(self.driver, 15)
        print("Браузер запущен успешно!")

    def parse_by_keyword(self, keyword: str, max_products: int = 50) -> list:
        """Парсинг товаров по ключевому слову"""
        print(f"🔍 Поиск товаров по запросу: '{keyword}'")

        try:
            search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(keyword)}&sort=popular"
            print(f"🌐 Переход по URL: {search_url}")

            self.driver.get(search_url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-nm-id]')))
            time.sleep(3)

            products = []
            page = 1

            while len(products) < max_products:
                print(f"\n📄 Обработка страницы {page}...")

                self._scroll_page()

                # Ищем карточки товаров, исключая карусель конструктора
                product_cards = self._get_valid_product_cards()

                if not product_cards:
                    print("❌ Карточки товаров не найдены")
                    break

                print(f"📦 Найдено карточек (после фильтрации): {len(product_cards)}")

                new_products = self._parse_cards_safely(product_cards, max_products - len(products))
                products.extend(new_products)

                print(f"✅ Успешно спаршено: {len(new_products)} товаров")
                print(f"📊 Всего собрано: {len(products)}/{max_products}")

                if len(products) >= max_products:
                    print("🎯 Достигнут лимит товаров")
                    break

                if not self._go_to_next_page():
                    print("⏹️ Следующая страница не найдена")
                    break

                page += 1
                time.sleep(2)

            return products

        except Exception as e:
            print(f"❌ Ошибка при парсинге: {e}")
            return []

    def parse_by_seller(self, seller_id: str, max_products: int = 50) -> list:
        """Парсинг товаров по продавцу"""
        print(f"🔍 Поиск товаров продавца: {seller_id}")

        try:
            seller_url = f"https://www.wildberries.ru/seller/{seller_id}"
            print(f"🌐 Переход по URL: {seller_url}")

            self.driver.get(seller_url)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-nm-id]')))
            time.sleep(3)

            products = []
            page = 1

            while len(products) < max_products:
                print(f"\n📄 Обработка страницы {page}...")

                self._scroll_page()

                # Ищем карточки товаров, исключая карусель конструктора
                product_cards = self._get_valid_product_cards()

                if not product_cards:
                    print("❌ Карточки товаров не найдены")
                    break

                print(f"📦 Найдено карточек (после фильтрации): {len(product_cards)}")

                new_products = self._parse_cards_safely(product_cards, max_products - len(products))
                products.extend(new_products)

                print(f"✅ Успешно спаршено: {len(new_products)} товаров")

                if len(products) >= max_products:
                    break

                if not self._go_to_next_page():
                    break

                page += 1
                time.sleep(2)

            return products

        except Exception as e:
            print(f"❌ Ошибка при парсинге продавца: {e}")
            return []

    def _get_valid_product_cards(self):
        """Получение валидных карточек товаров (исключая карусель конструктора)"""
        try:
            # Находим все карточки с data-nm-id
            all_cards = self.driver.find_elements(By.CSS_SELECTOR, 'article[data-nm-id]')

            # Фильтруем карточки из карусели конструктора
            valid_cards = []

            for card in all_cards:
                if self._is_valid_card(card):
                    valid_cards.append(card)

            # Логируем статистику
            filtered_count = len(all_cards) - len(valid_cards)
            if filtered_count > 0:
                print(f"    🚫 Отфильтровано товаров из карусели: {filtered_count}")

            return valid_cards

        except Exception as e:
            print(f"    ⚠️ Ошибка при фильтрации карточек: {e}")
            return []

    def _is_valid_card(self, card):
        """Проверяет, является ли карточка валидной (не из карусели конструктора)"""
        try:
            # Игнорируем карточки из карусели конструктора
            constructor_selectors = [
                '.catalog-page__constructor-carousel',
                '.j-constructor-carousel',
                '[class*="constructor-carousel"]'
            ]

            # Проверяем, находится ли карточка внутри карусели конструктора
            for selector in constructor_selectors:
                try:
                    # Ищем родительский элемент с классом карусели
                    constructor_parent = card.find_element(By.XPATH,
                                                           f"./ancestor::*[contains(@class, 'constructor-carousel') or contains(@class, 'catalog-page__constructor-carousel')]")
                    if constructor_parent:
                        return False
                except NoSuchElementException:
                    continue

            # Дополнительная проверка по структуре карточки
            card_classes = card.get_attribute('class')
            if card_classes and any(keyword in card_classes for keyword in ['constructor', 'carousel']):
                return False

            return True

        except Exception as e:
            # В случае ошибки считаем карточку валидной (лучше собрать лишнее, чем пропустить)
            print(f"      ⚠️ Ошибка проверки карточки: {e}")
            return True

    def _parse_cards_safely(self, cards, max_count: int):
        """Безопасный парсинг карточек с обработкой ошибок"""
        products = []

        for i, card in enumerate(cards[:max_count]):
            try:
                product_info = self._extract_product_safely(card)
                if product_info:
                    products.append(product_info)
                    price_display = f"{product_info['price']:,} руб." if product_info['price'] else "нет цены"
                    print(f"  ✅ {i + 1}. {product_info['name'][:50]}... - {price_display}")

            except Exception as e:
                print(f"  ❌ Ошибка карточки {i + 1}: {str(e)[:100]}...")
                continue

        return products

    def _extract_product_safely(self, card):
        """Безопасное извлечение информации о товаре"""
        try:
            # Базовые данные из атрибутов
            product_id = card.get_attribute('data-nm-id')
            if not product_id:
                return None

            # Основная информация
            product_info = {
                'product_id': product_id,
                'product_url': self._safe_get_attribute(card, 'a.j-card-link', 'href'),
                'name': self._safe_get_text(card, '.product-card__name'),
                'brand': self._safe_get_text(card, '.product-card__brand'),
                'price': self._safe_extract_price(card),
                'photo_url': self._safe_get_photo_url(card),
                'discount': self._safe_get_text(card, '.product-card__tip--sale'),
                'rating': self._safe_get_text(card, '.address-rate-mini'),
                'reviews_count': self._safe_get_text(card, '.product-card__count')
            }

            # Формируем полное название
            product_info['full_name'] = f"{product_info['brand']} {product_info['name']}".strip()
            if product_info['name'].startswith('/'):
                product_info['name'] = product_info['name'][2:]
            # Проверяем, что есть минимально необходимая информация
            if not product_info['product_url'] or not product_info['name']:
                return None

            return product_info

        except Exception as e:
            print(f"    ⚠️ Ошибка извлечения данных: {e}")
            return None

    def _safe_get_attribute(self, element, selector, attribute):
        """Безопасное получение атрибута элемента"""
        try:
            el = element.find_element(By.CSS_SELECTOR, selector)
            return el.get_attribute(attribute)
        except NoSuchElementException:
            return ""

    def _safe_get_text(self, element, selector):
        """Безопасное получение текста элемента"""
        try:
            el = element.find_element(By.CSS_SELECTOR, selector)
            return el.text.strip()
        except NoSuchElementException:
            return ""

    def _safe_extract_price(self, card):
        """Безопасное извлечение цены"""
        try:
            # Пробуем разные селекторы для цены
            price_selectors = [
                '.price__lower-price',
                '.lower-price',
                '.final-price',
                '.price',
                '.product-card__price'
            ]

            for selector in price_selectors:
                try:
                    price_element = card.find_element(By.CSS_SELECTOR, selector)
                    price_text = price_element.text
                    price = self._parse_price(price_text)
                    if price:
                        return price
                except NoSuchElementException:
                    continue

            return None

        except Exception:
            return None

    def _safe_get_photo_url(self, card):
        """Безопасное получение URL фото"""
        try:
            img_element = card.find_element(By.CSS_SELECTOR, 'img.j-thumbnail')
            return (
                    img_element.get_attribute('data-src-pb') or
                    img_element.get_attribute('src') or
                    ""
            )
        except NoSuchElementException:
            return ""

    def _parse_price(self, price_text):
        """Парсинг цены из текста"""
        try:
            numbers = re.findall(r'\d+', price_text.replace(' ', '').replace('₽', ''))
            return int(''.join(numbers)) if numbers else None
        except:
            return None

    def _scroll_page(self):
        """Прокрутка страницы"""
        try:
            print("    📜 Прокрутка страницы...")

            scroll_pause_time = 1
            scroll_height = self.driver.execute_script("return document.body.scrollHeight")
            current_position = 0
            scroll_step = 500

            while current_position < scroll_height:
                self.driver.execute_script(f"window.scrollTo(0, {current_position});")
                current_position += scroll_step
                time.sleep(scroll_pause_time)

                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height > scroll_height:
                    scroll_height = new_height

            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)

        except Exception as e:
            print(f"    ⚠️ Ошибка прокрутки: {e}")

    def _go_to_next_page(self):
        """Переход на следующую страницу"""
        try:
            print("    🔄 Поиск следующей страницы...")

            pagination_selectors = [
                '.pagination__next',
                '.pagination-next',
                'a.pagination-next',
                '.j-next-page'
            ]

            for selector in pagination_selectors:
                try:
                    next_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if next_btn.is_enabled():
                        self.driver.execute_script("arguments[0].click();", next_btn)
                        time.sleep(3)
                        self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[data-nm-id]')))
                        print("    ✅ Переход на следующую страницу")
                        return True
                except:
                    continue

            print("    ❌ Кнопка следующей страницы не найдена")
            return False

        except Exception as e:
            print(f"    ❌ Ошибка перехода на след. страницу: {e}")
            return False

    def save_to_excel(self, products, filename=None):
        """Сохранение результатов в Excel"""
        if not products:
            print("❌ Нет данных для сохранения")
            return False

        if not filename:
            timestamp = int(time.time())
            filename = f"wildberries_products_{timestamp}.xlsx"

        try:
            df = pd.DataFrame(products)

            # Убираем дубликаты
            initial_count = len(df)
            df = df.drop_duplicates(subset=['product_id'], keep='first')
            final_count = len(df)

            if initial_count != final_count:
                print(f"⚠️ Удалено дубликатов: {initial_count - final_count}")

            # Сохраняем в Excel
            df = df[["product_id", "product_url", "brand", "name", "price", "discount", "rating", "reviews_count", "full_name", "photo_url"]]
            redact(df, filename)
            print(f"\n🎉 ДАННЫЕ УСПЕШНО СОХРАНЕНЫ!")
            print(f"📁 Файл: {filename}")
            print(f"📊 Товаров: {len(df)}")

            if not df.empty:
                print(f"💰 Диапазон цен: {df['price'].min():,} - {df['price'].max():,} руб.")
                print(f"⭐ Уникальных брендов: {df['brand'].nunique()}")

            return True

        except Exception as e:
            print(f"❌ Ошибка при сохранении файла: {e}")
            return False

    def close(self):
        """Закрытие браузера"""
        if self.driver:
            self.driver.quit()
            print("\n👋 Браузер закрыт")
