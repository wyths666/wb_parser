import time
from parser import WildberriesRobustParser


def main():
    """Основная функция"""
    print("=" * 60)
    print("           🛍️ ПАРСЕР WILDBERRIES (С ФИЛЬТРАЦИЕЙ)")
    print("=" * 60)
    print("⚡ Игнорирует товары из карусели конструктора")
    print("=" * 60)

    parser = WildberriesRobustParser(headless=False)

    try:
        while True:
            print("\n🎯 Выберите тип парсинга:")
            print("1. 🔍 Поиск по ключевому слову")
            print("2. 👤 Поиск по продавцу (ID)")
            print("3. 🚪 Выход")

            choice = input("\nВаш выбор (1-3): ").strip()

            if choice == '1':
                keyword = input("Введите ключевое слово для поиска: ").strip()
                if keyword:
                    max_products = input("Сколько товаров собрать (по умолчанию 50): ").strip()
                    max_products = int(max_products) if max_products.isdigit() else 50

                    print(f"\n🚀 Начинаем парсинг...")
                    products = parser.parse_by_keyword(keyword, max_products)

                    if products:
                        filename = f"wildberries_{keyword.replace(' ', '_')}_{int(time.time())}.xlsx"
                        parser.save_to_excel(products, filename)
                    else:
                        print("❌ Не удалось найти товары")

            elif choice == '2':
                seller_id = input("Введите ID продавца: ").strip()
                if seller_id:
                    max_products = input("Сколько товаров собрать (по умолчанию 50): ").strip()
                    max_products = int(max_products) if max_products.isdigit() else 50

                    print(f"\n🚀 Начинаем парсинг...")
                    products = parser.parse_by_seller(seller_id, max_products)

                    if products:
                        filename = f"wildberries_seller_{seller_id}_{int(time.time())}.xlsx"
                        parser.save_to_excel(products, filename)
                    else:
                        print("❌ Не удалось найти товары продавца")

            elif choice == '3':
                print("👋 Выход из программы...")
                break

            else:
                print("❌ Неверный выбор, попробуйте снова")

            continue_choice = input("\nПродолжить работу? (y/n): ").strip().lower()
            if continue_choice != 'y':
                print("👋 До свидания!")
                break

    except KeyboardInterrupt:
        print("\n⏹️ Программа прервана пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    finally:
        parser.close()


if __name__ == "__main__":
    main()