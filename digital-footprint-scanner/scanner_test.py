import os
import argparse
import sys
from sources.maigret_tool import run_maigret_logic
from sources.phone_tool import run_phone_logic
BOLD = "\033[1m"
RESET = "\033[0m"
YELLOW = "\033[93m"


def main():
    parser = argparse.ArgumentParser(description="Сканер цифрового следа")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--username", type=str, help="Имя пользователя для поиска")
    group.add_argument("--email", type=str, help="Email для поиска (в разработке)")
    group.add_argument("--phone", type=str, help="Номер телефона для поиска (в разработке)")

    parser.add_argument("--format", type=str, default="txt", choices=["txt", "json", "csv", "all"],
                        help="Формат сохранения отчета")
    parser.add_argument("--no-save", action="store_true", help="Не сохранять отчет")

    args = parser.parse_args()

    if args.username:
        query, search_type = args.username, "username"
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

    if search_type == "username":
        run_maigret_logic(query, formats=args.format, output_dir=report_dir)
        if not args.no_save:
            print(f"\n{YELLOW}[ИНФО] Отчеты сохранены в папку {report_dir}/{RESET}")
    elif search_type == "phone":
        run_phone_logic(query, output_dir=report_dir)
    else:
        print(f"{YELLOW}[*] Поиск по {search_type} пока в разработке...{RESET}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход из программы.")
        sys.exit(0)
    except Exception as e:
        print(f"\nПроизошла ошибка: {e}")
        sys.exit(1)