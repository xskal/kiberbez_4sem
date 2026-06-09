import os
import argparse
import sys
import glob
from dotenv import load_dotenv
load_dotenv()
from sources.maigret_tool import run_maigret_logic
from sources.phone_tool import run_phone_logic
from sources.holehe_tool import run_email_scan
from sources.tor_bridges_tool import update_tor_bridges

BOLD = "\033[1m"
RESET = "\033[0m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
CYAN = "\033[96m"

def show_final_report(report_dir, search_type, query, ext="txt"):
    print(f"\n{CYAN}{BOLD}" + "=" * 55)
    print("      АГРЕГАЦИЯ РЕЗУЛЬТАТОВ И ССЫЛКИ НА ИСТОЧНИКИ")
    print("=" * 55 + f"{RESET}")

    search_ext = "*" if ext == "all" else ext
    found_files = []

    if search_type == "phone":
        clean_phone = "".join(filter(str.isdigit, query))
        found_files = glob.glob(os.path.join(report_dir, f"phone_osint_*{clean_phone}*.{search_ext}"))
    elif search_type == "username":
        found_files = glob.glob(os.path.join(report_dir, f"*{query}*.{search_ext}"))
    elif search_type == "email":
        found_files = glob.glob(os.path.join(report_dir, f"*{query}*.{search_ext}")) + \
                      glob.glob(os.path.join(report_dir, f"*email*.{search_ext}"))

    if found_files:
        latest_report = max(found_files, key=os.path.getmtime)
        print(f"{GREEN}[+] Обнаружен структурированный отчет: {os.path.basename(latest_report)}{RESET}\n")
        print(f"{BOLD}[ СВОДКА НАЙДЕННЫХ ДАННЫХ И ССЫЛОК ]{RESET}")
        print("-" * 55)

        try:
            with open(latest_report, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line_str = line.strip()
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
    group.add_argument("--update-bridges", type=str, help="Обновить мосты WebTunnel Tor (передайте блок текста мостов)")
    parser.add_argument("--format", type=str, default="txt", choices=["txt", "json", "csv", "all"], help="Формат сохранения отчета")
    parser.add_argument("--no-save", action="store_true", help="Не сохранять отчет на диск")

    args = parser.parse_args()

    if args.update_bridges:
        print(f"\n{BOLD}[*] Запущено обновление мостов Tor...{RESET}")
        if update_tor_bridges(args.update_bridges):
            print(f"{YELLOW}[ИНФО] При следующем сканировании почты Tor запустится с новыми мостами.{RESET}\n")
        sys.exit(0)

    if not (args.username or args.email or args.phone):
        parser.error("Необходимо указать один из параметров: --username, --email, --phone или --update-bridges")

    if args.username:
        query, search_type = args.username, "username"
    elif args.email:
        query, search_type = args.email, "email"
    else:
        query, search_type = args.phone, "phone"

    report_dir = "reports"
    if args.no_save:
        actual_output_dir = None
    else:
        actual_output_dir = report_dir
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)

    print(f"\n{BOLD}[*] Начинаю поиск...{RESET}")
    print(f"[*] Объект: {query} | Тип: {search_type}")
    print("-" * 50)

    if search_type == "username":
        run_maigret_logic(query, formats=args.format, output_dir=actual_output_dir)
        if not args.no_save:
            print(f"\n{YELLOW}[ИНФО] Отчеты Maigret сохранены в папку {report_dir}/{RESET}")
    elif search_type == "phone":
        run_phone_logic(query, formats=args.format, output_dir=actual_output_dir)
    elif search_type == "email":
        run_email_scan(query, formats=args.format, output_dir=actual_output_dir)

    if not args.no_save:
        show_final_report(report_dir, search_type, query, ext=args.format)
        print(f"{BOLD}{GREEN}[+] Задача успешно завершена. Все данные агрегированы.{RESET}")
    else:
        print(f"\n{BOLD}{GREEN}[+] Задача завершена. Данные выведены в консоль (без сохранения на диск).{RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход из программы.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПроизошла критическая ошибка: {e}")
        sys.exit(1)