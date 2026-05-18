import subprocess
import os


def run_maigret_logic(nickname, formats="txt", output_dir="reports"):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(base_dir, "bin")

    tor_exe = os.path.join(bin_dir, "tor.exe")
    maigret_exe = os.path.join(bin_dir, "maigret_standalone.exe")

    if not os.path.exists(maigret_exe):
        print("\033[91m[!] Файл maigret_standalone.exe не найден!\033[0m")
        return

    custom_env = os.environ.copy()
    custom_env["PYTHONIOENCODING"] = "utf-8"

    # ПУТЬ ОТЧЁТА
    abs_output_dir = os.path.abspath(output_dir)
    report_flags = ["--folder", abs_output_dir]

    if formats in ["txt", "all"]:
        report_flags.append("--txt")
    if formats in ["json", "all"]:
        report_flags.append("--json")
    if formats in ["csv", "all"]:
        report_flags.append("--csv")
    '''
    # НУЖНЫЕ САЙТЫ
    notor_sites = [
        "--site", "VK",
        "--site", "OK",
        "--site", "Max"
    ]

    base_cmd = [
                   maigret_exe, nickname,
                   "--timeout", "40",
                   "--retries", "3",
                   "--print-errors",
                   "--max-connections", "3",
                   "--cloudflare-bypass",
                   "-n", "10"
               ] + notor_sites + report_flags
#--------------------------------------------------------------------------------------------
    print("\n\033[94m[1/2] Запуск прямого сканирования (БЕЗ Tor)...\033[0m")
    subprocess.run(base_cmd, cwd=bin_dir, env=custom_env)
    '''
    if os.path.exists(tor_exe):
        print("\n\033[93m[2/2] Подключение к сети TOR...\033[0m")
        tor_proc = subprocess.Popen(
            [tor_exe, "-f", "torrc.txt"],
            cwd=bin_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        for line in tor_proc.stdout:
            if "Bootstrapped 100%" in line or "Done" in line:
                print("\033[92m[+] Tor подключен!\033[0m")
                break

        print("\033[94m[*] Запуск сканирования через TOR...\033[0m")
        tor_sites = [
            "--site", "VK",
            "--site", "OK",
            "--site", "MAX",
            "--site", "Telegram",
            "--site", "YouTube",
            "--site", "Instagram",
            "--site", "Twitter",
            "--site", "Reddit",
            "--site", "Habr",
            "--site", "TikTok",
            "--site", "Discord",
            "--site", "Steam",
            "--site", "Tinder",
            "--site", "Badoo",
            "--site", "Facebook",
            "--site", "LinkedIn",
            "--site", "GitHub",
            "--site", "Wikipedia",
            "--site", "Pinterest",
            "--site", "Spotify",
            "--site", "Twitch",
            "--site", "YandexReviews",
            "--site", "Fandom",
            "--site", "Snapchat",
            "--site", "YandexZen",
            "--site", "Pikabu",
            "--site", "Kick",
            "--site", "Drive2",
            "--site", "WhatsApp",
            "--site", "Avito",
            "--site", "Pastebin",
            "--site", "eBay",
            "--site", "Amazon",
            "--site", "Patreon",
            "--site", "StackOverflow",
            "--site", "Behance",
            "--site", "Dribbble",
        ]
        tor_cmd = [
            maigret_exe, nickname,
            "--timeout", "60",
            "--retries", "3",
            "--max-connections", "7",
            "--cloudflare-bypass",
            "-n", "10",
            "--proxy", "socks5://127.0.0.1:9050"
        ] + tor_sites + report_flags

        subprocess.run(tor_cmd, cwd=bin_dir, env=custom_env)

        tor_proc.terminate()
        tor_proc.wait()
    else:
        print("\033[91m[!] Tor не найден. Пропуск второго этапа.\033[0m")