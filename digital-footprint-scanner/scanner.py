import os
import argparse
import sys
import glob
from sources.maigret_tool import run_maigret_logic
from sources.phone_tool import run_phone_logic
from sources.holehe_tool import run_maigret_logic
from sources.tor_bridges_tool import update_tor_bridges

# Цветовая палитра для красивого вывода куратору
BOLD = "\033[1m"
RESET = "\033[0m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"


def show_final_report(report_dir, search_type, query):
    """
    Выполняет требование куратора: агрегирует данные из изолированных
    отчетов утилит и выводит ссылки на найденные источники.
    """
    print(f"\n{CYAN}{BOLD}" + "=" * 55)
    print("      АГРЕГАЦИЯ РЕЗУЛЬТАТОВ И ССЫЛКИ НА ИСТОЧНИКИ")
    print("=" * 55 + f"{RESET}")

    found_files = []

    # Ищем файлы отчетов в зависимости от того, что сканировали
    if search_type == "phone":
        clean_phone = "".join(filter(str.isdigit, query))
        found_files = glob.glob(os.path.join(report_dir, f"phone_osint_*{clean_phone}*.txt"))
    elif search_type == "username":
        found_files = glob.glob(os.path.join(report_dir, f"*{query}*.txt"))
    elif search_type == "email":
        # Если email_tool сохраняет отчёты (например, по названию email или email_report)
        found_files = glob.glob(os.path.join(report_dir, f"*{query}*.txt")) + \
                      glob.glob(os.path.join(report_dir, "*email*.txt"))

    if found_files:
        # Берем самый свежий измененный файл отчета
        latest_report = max(found_files, key=os.path.getmtime)
        print(f"{GREEN}[+] Обнаружен структурированный отчет: {os.path.basename(latest_report)}{RESET}\n")
        print(f"{BOLD}[ СВОДКА НАЙДЕННЫХ ДАННЫХ И ССЫЛОК ]{RESET}")
        print("-" * 55)

        # Читаем файл отчета и агрегируем только важные строки (результаты и ссылки)
        try:
            with open(latest_report, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_str = line.strip()
                    # Выдергиваем строки с веб-ссылками, маркерами списков и ключевой инфой
                    if "http" in line_str or "─" in line_str or "•" in line_str or " Регион" in line_str or " Оператор" in line_str:
                        print(line_str)
        except Exception as e:
            print(f"{YELLOW}[!] Не удалось прочитать файл отчета для агрегации: {e}{RESET}")
    else:
        print(f"{YELLOW}[!] Файл отчета на диске не найден. Проверьте вывод утилит выше.{RESET}")

    print(f"\n{CYAN}" + "=" * 55 + f"{RESET}\n")


def main():
    parser = argparse.ArgumentParser(description="Сканер цифрового следа (OSINT)")
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument("--username", type=str, help="Имя пользователя для поиска через Maigret")
    group.add_argument("--email", type=str, help="Email для поиска утечек и профилей")
    group.add_argument("--phone", type=str, help="Номер телефона для OSINT-анализа")
    group.add_argument("--update-bridges", type=str,
                       help="Обновить мосты WebTunnel Tor (передайте блок текста мостов)")
    parser.add_argument("--format", type=str, default="txt", choices=["txt", "json", "csv", "all"],
                        help="Формат сохранения отчета")
    parser.add_argument("--no-save", action="store_true", help="Не сохранять отчет на диск")

    args = parser.parse_args()

    if args.update_bridges:
        print(f"\n{BOLD}[*] Запущено обновление мостов Tor...{RESET}")
        if update_tor_bridges(args.update_bridges):
            print(f"{YELLOW}[ИНФО] При следующем сканировании почты Tor запустится с новыми мостами.{RESET}\n")
        sys.exit(0)

    # Проверяем, ввёл ли обычный пользователь хоть что-то для поиска
    if not (args.username or args.email or args.phone):
        parser.error("Необходимо указать один из параметров: --username, --email, --phone или --update-bridges")

    if args.username:
        query, search_type = args.username,"username"
    elif args.email:
        query, search_type = args.email, "email"
    else:
        query, search_type = args.phone, "phone"

    report_dir = "reports"
    if not args.no_save and not os.path.exists(report_dir):
        os.makedirs(report_dir)

    print(f"\n{BOLD}[*] Начинаю поиск...{RESET}")
    print(f"[*] Объект: {query} | Тип: {search_type}")
    print("-" * 50)

    # Запуск модулей сканирования
    if search_type == "username":
        run_maigret_logic(query, formats=args.format, output_dir=report_dir)
        if not args.no_save:
            print(f"\n{YELLOW}[ИНФО] Отчеты Maigret сохранены в папку {report_dir}/{RESET}")

    elif search_type == "phone":
        run_phone_logic(query, output_dir=report_dir)

    elif search_type == "email":
        run_maigret_logic(query, output_dir=report_dir)

    # Блок агрегации данных и вывода ссылок для куратора
    if not args.no_save:
        show_final_report(report_dir, search_type, query)
        print(f"{BOLD}{GREEN}[+] Задача успешно завершена. Все данные агрегированы.{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход из программы.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПроизошла критическая ошибка: {e}")
        sys.exit(1)
