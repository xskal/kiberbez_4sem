import subprocess
import os

# Цвета для вывода
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"

def run_maigret_logic(nickname):
    """Логика запуска Maigret: сначала напрямую, затем через Tor."""
    print("pososi")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(base_dir, "bin")
    
    tor_exe = os.path.join(bin_dir, "tor.exe")
    maigret_exe = os.path.join(bin_dir, "maigret_standalone.exe")

    if not os.path.exists(maigret_exe):
        return [{"risk_level": "error", "description": "Файл maigret_standalone.exe не найден!"}]

    try:
        # --- ЭТАП 1: ПРЯМОЙ ПОИСК (БЕЗ TOR) ---
        print(f"{BLUE}[1/2] Запуск прямого сканирования (БЕЗ Tor)...{RESET}")
        
        direct_cmd = [
            maigret_exe, nickname,
            "--timeout", "30", # Напрямую можно таймаут поменьше
            "--retries", "2",
            "--print-errors",
            "--max-connections", "10",
            "--cloudflare-bypass",
            "-n", "10"
        ]
        
        # Запускаем напрямую
        subprocess.run(direct_cmd, cwd=bin_dir)
        print(f"{GREEN}[+] Прямое сканирование завершено.{RESET}\n")

        # --- ЭТАП 2: ПОИСК ЧЕРЕЗ TOR ---
        if not os.path.exists(tor_exe):
            return [{"risk_level": "warning", "description": "Tor не найден, пропускаю второй этап."}]

        print(f"{YELLOW}[2/2] Запуск сканирования через TOR прокси...{RESET}")
        
        tor_proc = subprocess.Popen(
            [tor_exe, "-f", "torrc.txt"],
            cwd=bin_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        # Ожидание Tor
        for line in tor_proc.stdout:
            if "Bootstrapped 100%" in line or "Done" in line:
                print(f"{GREEN}[+] Tor подключен! Довыполняю поиск...{RESET}")
                break
        
        tor_cmd = [
            maigret_exe, nickname,
            "--proxy", "socks5://127.0.0.1:9050",
            "--timeout", "60",
            "--retries", "2", 
            "--print-errors",
            "--max-connections", "10",
            "--cloudflare-bypass",
            "-n", "10"
        ]
        
        subprocess.run(tor_cmd, cwd=bin_dir)
        
        # Завершаем Tor
        tor_proc.terminate()
        tor_proc.wait()
        
        return [{"risk_level": "info", "description": "Глубокое сканирование (Прямое + Tor) завершено."}]

    except KeyboardInterrupt:
        print(f"\n{RED}[!] Процесс прерван пользователем.{RESET}")
        # Если Tor запущен, пытаемся его закрыть
        if 'tor_proc' in locals() and tor_proc:
            tor_proc.terminate()
        raise KeyboardInterrupt
    except Exception as e:
        return [{"risk_level": "high", "description": f"Ошибка в MaigretTool: {e}"}]
