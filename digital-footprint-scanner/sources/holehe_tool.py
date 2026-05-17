import subprocess
import os
import sys

def run_email_scan(email):
    # Определение путей (с поддержкой сборки в PyInstaller .exe через sys._MEIPASS)
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
    bin_dir = os.path.join(base_dir, "bin")

    tor_exe = os.path.join(bin_dir, "tor.exe")
    holehe_exe = os.path.join(bin_dir, "holehe.exe")

    if not os.path.exists(holehe_exe):
        print("\033[91m[!] Файл holehe.exe не найден!\033[0m")
        return

    if os.path.exists(tor_exe):
        print("\n\033[93m[1/2] Подключение к сети TOR...\033[0m")
        tor_proc = subprocess.Popen(
            [tor_exe, "-f", "torrc.txt"],
            cwd=bin_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Чтение логов Tor до полной инициализации (строго по вашему макету)
        for line in tor_proc.stdout:
            if "Bootstrapped 100%" in line or "Done" in line:
                print("\033[92m[+] Tor подключен!\033[0m")
                break

        print("\033[94m[2/2] Запуск сканирования почты через Holehe...\033[0m")
        
        # Формируем аргументы для holehe
        holehe_cmd = [
            holehe_exe, email,
            "--only-used"
        ]

        # Запускаем holehe, вшивая кодировку и SOCKS5-прокси Тора прямо в окружение команды
        subprocess.run(
            holehe_cmd, 
            cwd=bin_dir, 
            env={
                **os.environ, 
                "PYTHONIOENCODING": "utf-8", 
                "HTTP_PROXY": "socks5://127.0.0.1:9050", 
                "HTTPS_PROXY": "socks5://127.0.0.1:9050"
            }
        )

        # Отключаем Tor (строго по вашему макету)
        tor_proc.terminate()
        tor_proc.wait()
    else:
        print("\033[91m[!] Tor не найден. Сканирование почты невозможно.\033[0m")
