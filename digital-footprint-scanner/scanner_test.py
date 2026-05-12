import os
import argparse
import subprocess
from datetime import datetime
from sources.maigret_tool import run_maigret_logic
# --- Цветовая разметка (для красоты) ---
YELLOW = "\033[93m"
BOLD = "\033[1m"
RESET = "\033[0m"
GREEN = "\033[92m"
RED = "\033[91m"



# --- Основной класс сканнера ---
class DigitalFootprintScanner:
    def __init__(self):
        self.results = []

    def scan(self, query, search_type):
        """Диспетчер задач в зависимости от типа поиска."""
        print(f"\n{BOLD}[*] Начинаю поиск цифрового следа...{RESET}")
        print(f"[*] Объект: {query} | Тип: {search_type}")
        print("-" * 50)

        if search_type == "username":
            self._scan_username(query)
        elif search_type == "email":
            self._scan_email(query)
        elif search_type == "phone":
            self._scan_phone(query)

    def _scan_username(self, nick):
        # Здесь в будущем будут твои быстрые модули из sources
        print(f"{YELLOW}[*] Поиск по никнейму...{RESET}")
        res = run_maigret_logic(nick)
        self.results.extend(res)

    def _scan_email(self, email):
        print(f"{YELLOW}[*] Поиск по Email (модули в разработке)...{RESET}")
        self.results.append({"risk_level": "info", "description": f"Email {email} проверен (заглушка)."})

    def _scan_phone(self, phone):
        print(f"{YELLOW}[*] Поиск по телефону (модули в разработке)...{RESET}")
        self.results.append({"risk_level": "info", "description": f"Телефон {phone} проверен (заглушка)."})

    def print_results(self):
        print(f"\n{BOLD}--- РЕЗУЛЬТАТЫ ---{RESET}")
        for r in self.results:
            icon = "✅" if r['risk_level'] == "info" else "❌"
            print(f"{icon} {r['description']}")

    # Заглушки для функций сохранения (чтобы argparse не ругался)
    def save_report_txt(self, path): print(f"[ИНФО] Отчет TXT сохранен: {path}")
    def save_report_json(self, path): pass
    def save_report_csv(self, path): pass


# --- Главная функция запуска ---
def main():
    parser = argparse.ArgumentParser(
        description="Автоматизированное средство поиска цифрового следа в сети Интернет",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  python scanner.py --username john_doe
  python scanner.py --email user@example.com
  python scanner.py --phone +79991234567
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--username", type=str, help="Имя пользователя для поиска")
    group.add_argument("--email", type=str, help="Email для поиска")
    group.add_argument("--phone", type=str, help="Номер телефона для поиска")
    
    parser.add_argument("--format", type=str, default="txt",
                       choices=["txt", "json", "csv", "all"],
                       help="Формат сохранения отчета (по умолчанию: txt)")
    parser.add_argument("--output", type=str, default=None,
                       help="Имя файла отчета (без расширения)")
    parser.add_argument("--no-save", action="store_true",
                       help="Не сохранять отчет в файл")
    
    args = parser.parse_args()

    # Определяем тип и значение
    if args.username:
        query, search_type = args.username, "username"
    elif args.email:
        query, search_type = args.email, "email"
    else:
        query, search_type = args.phone, "phone"
    
    # Папка для отчетов
    report_dir = "reports"
    if not args.no_save and not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    scanner = DigitalFootprintScanner()
    scanner.scan(query, search_type)
    scanner.print_results()
    
    # Логика сохранения
    if not args.no_save:
        base_name = args.output if args.output else f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if args.format in ["txt", "all"]:
            scanner.save_report_txt(os.path.join(report_dir, f"{base_name}.txt"))
        
        print(f"\n{YELLOW}{BOLD}[ИНФО] По умолчанию отчет сохраняется в папку reports/.{RESET}")
        
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nВыход из программы.")
        os._exit(0)