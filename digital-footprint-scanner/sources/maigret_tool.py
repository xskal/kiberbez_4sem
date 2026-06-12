import subprocess
import os
import tempfile
import shutil


def generate_recommendations(found_sites, report_path=None):
    high_risk_sites = {"VK", "OK", "Telegram", "Avito", "Drive2", "YandexReviews", "YandexZen"}
    medium_risk_sites = {"Instagram", "Twitter", "Reddit", "Habr", "GitHub", "StackOverflow",
                         "Discord", "Steam", "YouTube", "Pinterest", "Pikabu", "Facebook", "LinkedIn"}

    detected_high = [s for s in found_sites if s in high_risk_sites]
    detected_medium = [s for s in found_sites if s in medium_risk_sites]
    detected_low = [s for s in found_sites if s not in high_risk_sites and s not in medium_risk_sites]

    rec_text = []
    rec_text.append("\n" + "=" * 60)
    rec_text.append(" 🛡️ АВТОМАТИЧЕСКИЕ РЕКОМЕНДАЦИИ ПО БЕЗОПАСНОСТИ ЦИФРОВОГО СЛЕДА")
    rec_text.append("=" * 60)

    if detected_high:
        rec_text.append(f"\n🔴 [КРИТИЧЕСКИЙ РИСК] Найдены СНГ-профили: {', '.join(detected_high)}")
        rec_text.append("  ↳ Угроза: Эти платформы жестко привязаны к личности, геолокации или номерам телефонов.")
        rec_text.append("  ↳ Рекомендация: Измените никнейм в данных сервисах на случайный (уникальный для каждого).")
        rec_text.append("  ↳               Скройте профили настройками приватности, удалите старые отзывы/объявления.")

    if detected_medium:
        rec_text.append(f"\n🟡 [СРЕДНИЙ РИСК] Найдена социальная/проф. активность: {', '.join(detected_medium)}")
        rec_text.append(
            "  ↳ Угроза: Высокий риск утечки информации о хобби, связях, технологическом стеке или месте работы.")
        rec_text.append("  ↳ Рекомендация: Закройте списки друзей и подписок. Не публикуйте sensitive-информацию.")

    if detected_low and not detected_high and not detected_medium:
        rec_text.append(f"\n🟢 [НИЗКИЙ РИСК] Найдены только медиа/торговые площадки: {', '.join(detected_low)}")
        rec_text.append("  ↳ Угроза: Прямая деанонимизация маловероятна. Возможен сбор базовой карты интересов.")
        rec_text.append(
            "  ↳ Рекомендация: Соблюдайте базовую гигиену паролей, включите двухфакторную аутентификацию (2FA).")

    if not found_sites:
        rec_text.append("\n🎉 Ни одного упоминания никнейма на проверяемых сайтах не найдено.")
        rec_text.append("  ↳ Уровень угрозы: Минимальный. Цифровой след чист.")

    rec_text.append("\n" + "=" * 60 + "\n")

    final_output = "\n".join(rec_text)
    print(final_output)

    if report_path and os.path.exists(report_path):
        try:
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(final_output)
        except Exception as e:
            pass


def run_maigret_logic(nickname, formats="txt", output_dir="reports", quick_mode=False):
    os.system("chcp 65001 > nul")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    bin_dir = os.path.join(base_dir, "bin")

    tor_exe = os.path.join(bin_dir, "tor.exe")
    maigret_exe = os.path.join(bin_dir, "maigret_standalone.exe")

    if not os.path.exists(maigret_exe):
        print("\033[91m[!] Файл maigret_standalone.exe не найден!\033[0m")
        return

    custom_env = os.environ.copy()
    custom_env["PYTHONIOENCODING"] = "utf-8"

    is_temp_dir = False
    report_flags = []

    if output_dir is not None:
        abs_output_dir = os.path.abspath(output_dir)
        os.makedirs(abs_output_dir, exist_ok=True)
        report_flags = ["--folder", abs_output_dir]

        if formats in ["txt", "all"]: report_flags.append("--txt")
        if formats in ["json", "all"]: report_flags.append("--json")
        if formats in ["csv", "all"]: report_flags.append("--csv")
    else:
        abs_output_dir = tempfile.mkdtemp()
        is_temp_dir = True
        report_flags = ["--folder", abs_output_dir, "--txt"]


    if quick_mode:
        target_sites = [
            "--site", "VK", "--site", "Habr", "--site", "GitHub",
            "--site", "Telegram", "--site", "Reddit"
        ]
        timeout_val = "15"
        retries_val = "0"
    else:
        target_sites = [
            "--site", "VK", "--site", "OK", "--site", "MAX", "--site", "Telegram",
            "--site", "YouTube", "--site", "Instagram", "--site", "Twitter", "--site", "Reddit",
            "--site", "Habr", "--site", "TikTok", "--site", "Discord", "--site", "Steam",
            "--site", "Tinder", "--site", "Badoo", "--site", "Facebook", "--site", "LinkedIn",
            "--site", "GitHub", "--site", "Wikipedia", "--site", "Pinterest", "--site", "Spotify",
            "--site", "Twitch", "--site", "YandexReviews", "--site", "Fandom", "--site", "Snapchat",
            "--site", "YandexZen", "--site", "Pikabu", "--site", "Kick", "--site", "Drive2",
            "--site", "WhatsApp", "--site", "Avito", "--site", "Pastebin", "--site", "eBay",
            "--site", "Amazon", "--site", "Patreon", "--site", "StackOverflow", "--site", "Behance",
            "--site", "Dribbble",
        ]
        timeout_val = "60"
        retries_val = "3"

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

        for line in tor_proc.stdout:
            if "Bootstrapped 100%" in line or "Done" in line:
                print("\033[92m[+] Tor подключен!\033[0m")
                break

        print("\033[94m[2/2] Запуск сканирования через TOR...\033[0m")
        tor_cmd = [
                      maigret_exe, nickname,
                      "--timeout", timeout_val,
                      "--retries", retries_val,
                      "--max-connections", "7",
                      "--cloudflare-bypass",
                      "-n", "10",
                      "--proxy", "socks5://127.0.0.1:9050"
                  ] + target_sites + report_flags

        subprocess.run(tor_cmd, cwd=bin_dir, env=custom_env)

        tor_proc.terminate()
        tor_proc.wait()
    else:
        print("\033[91m[!] Tor не найден. Пропуск второго этапа.\033[0m")
        print("\033[93m[*] Запуск сканирования напрямую без TOR...\033[0m")

        dir_timeout = "15" if quick_mode else "40"
        dir_retries = "0" if quick_mode else "1"

        direct_cmd = [
                         maigret_exe, nickname,
                         "--timeout", dir_timeout,
                         "--retries", dir_retries,
                         "--max-connections", "3",
                         "--cloudflare-bypass",
                         "-n", "10"
                     ] + target_sites + report_flags

        subprocess.run(direct_cmd, cwd=bin_dir, env=custom_env)

    report_file_name = f"report_{nickname}.txt"
    report_file_path = os.path.join(abs_output_dir, report_file_name)

    domain_hints = {
        "telegram": "t.me",
        "vk": "vk.com",
        "ok": "ok.ru",
        "github": "github.com",
        "habr": "habr.com",
        "reddit": "reddit.com",
        "instagram": "instagram.com",
        "youtube": "youtube.com",
        "twitter": "twitter.com",
        "discord": "discord.com",
        "steam": "steamcommunity.com",
        "avito": "avito.ru",
        "pikabu": "pikabu.ru"
    }

    found_sites_detected = set()
    if os.path.exists(report_file_path):
        try:
            with open(report_file_path, "r", encoding="utf-8", errors="ignore") as f:
                report_content_lower = f.read().lower()

                for site in target_sites:
                    if site != "--site":
                        s_lower = site.lower()
                        hint = domain_hints.get(s_lower, s_lower)
                        if s_lower in report_content_lower or hint in report_content_lower:
                            found_sites_detected.add(site)

        except Exception as e:
            print(f"\033[93m[!] Ошибка чтения отчета для анализа: {e}\033[0m")

    if is_temp_dir:
        shutil.rmtree(abs_output_dir, ignore_errors=True)
        report_file_path = None

    generate_recommendations(list(found_sites_detected), report_path=report_file_path)