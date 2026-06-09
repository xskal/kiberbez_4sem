import subprocess
import os
import sys
import json


def get_tor_http_port(bin_dir):
    """Автоматически парсит torrc.txt и возвращает актуальный HTTP-порт."""
    torrc_path = os.path.join(bin_dir, "torrc.txt")
    if os.path.exists(torrc_path):
        try:
            with open(torrc_path, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip().startswith("HTTPTunnelPort"):
                        parts = line.split()
                        if len(parts) > 1:
                            return parts[1].split(":")[-1].strip()
        except:
            pass
    return "12000"


def generate_email_recommendations(found_services):
    """Формирует строковый блок рекомендаций на основе найденных сайтов."""
    high_risk_keywords = {"mail", "rambler", "yahoo", "google", "office", "ok", "blablacar", "deliveroo", "garmin",
                          "venmo", "avito", "sber", "tinkoff", "gosuslugi"}
    medium_risk_keywords = {"github", "gitlab", "instagram", "twitter", "discord", "snapchat", "pinterest", "tumblr",
                            "quora", "atlassian", "docker", "replit", "codepen", "codecademy", "amocrm", "zoho",
                            "pipedrive", "evernote", "slack"}

    detected_high = []
    detected_medium = []
    detected_low = []

    for svc in found_services:
        svc_lower = svc.lower().strip()
        if any(h in svc_lower for h in high_risk_keywords):
            detected_high.append(svc)
        elif any(m in svc_lower for m in medium_risk_keywords if m in svc_lower):
            detected_medium.append(svc)
        elif any(m in svc_lower for m in medium_risk_keywords):
            detected_medium.append(svc)
        else:
            detected_low.append(svc)

    rec_text = []
    rec_text.append("\n" + "=" * 60)
    rec_text.append(" 🛡️ АВТОМАТИЧЕСКИЕ РЕКОМЕНДАЦИИ ПО БЕЗОПАСНОСТИ EMAIL")
    rec_text.append("=" * 60)

    if detected_high:
        rec_text.append(
            f"\n🔴 [КРИТИЧЕСКИЙ РИСК] Email найден в критических СНГ/Почтовых/Финансовых сервисах: {', '.join(detected_high)}")
        rec_text.append(
            "  ↳ Угроза: Эти платформы напрямую связаны с вашей личностью, финансами или доступом к другим аккаунтам.")
        rec_text.append(
            "  ↳ Рекомендация: Включите двухфакторную аутентификацию (2FA). Используйте этот email строго для официальных целей.")

    if detected_medium:
        rec_text.append(
            f"\n🟡 [СРЕДНИЙ РИСК] Email привязан к соцсетям или платформам ИТ-разработки: {', '.join(detected_medium)}")
        rec_text.append(
            "  ↳ Угроза: Высокий риск утечки информации о вашем круге общения, хобби или технологическом стеке.")
        rec_text.append("  ↳ Рекомендация: Скройте отображение email в настройках приватности этих профилей.")

    if detected_low:
        rec_text.append(f"\n🟢 [НИЗКИЙ РИСК] Найдены развлекательные, медиа или CMS площадки: {', '.join(detected_low)}")
        rec_text.append(
            "  ↳ Угроза: Прямая деанонимизация маловероятна. Есть риск спам-рассылок в случае утечек баз этих сайтов.")
        rec_text.append("  ↳ Рекомендация: Используйте генераторы уникальных паролей и периодически заменяйте их.")

    if not found_services:
        rec_text.append("\n🎉 Этот email не найден ни в одной базе данных утилиты Holehe.")
        rec_text.append("  ↳ Уровень угрозы: Минимальный. Публичный след почты чист.")

    rec_text.append("\n" + "=" * 60 + "\n")
    return "\n".join(rec_text)


def run_email_scan(email, formats="txt", output_dir="reports"):
    os.system("chcp 65001 > nul")  # Фикс кодировки для Windows

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

        for line in tor_proc.stdout:
            if "Bootstrapped 100%" in line or "Done" in line:
                print("\033[92m[+] Tor подключен!\033[0m")
                break

        print("\033[94m[2/2] Запуск сканирования почты через Holehe...\033[0m")
        holehe_cmd = [holehe_exe, email, "--only-used"]

        tor_port = get_tor_http_port(bin_dir)
        proxy_url = f"http://127.0.0.1:{tor_port}"

        current_env = os.environ.copy()
        current_env["PYTHONIOENCODING"] = "utf-8"
        current_env["HTTP_PROXY"] = proxy_url
        current_env["HTTPS_PROXY"] = proxy_url
        current_env["http_proxy"] = proxy_url
        current_env["https_proxy"] = proxy_url

        found_services = []
        try:
            process = subprocess.run(
                holehe_cmd,
                cwd=bin_dir,
                env=current_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )

            print(process.stdout)

            raw_lines = process.stdout.split("\n")
            for line in raw_lines:
                clean_line = line.strip()
                if clean_line.startswith("[+]"):
                    site_name = clean_line.replace("[+]", "").strip().lower()
                    if site_name and "email used" not in site_name:
                        found_services.append(site_name)

            unique_services = list(set(found_services))
            recommendations = generate_email_recommendations(unique_services)

            # Сохраняем файлы ТОЛЬКО если output_dir не None (--no-save)
            if output_dir:
                abs_output_dir = os.path.abspath(output_dir)
                os.makedirs(abs_output_dir, exist_ok=True)

                safe_email = email.replace("@", "_at_")

                if formats in ["txt", "all"]:
                    report_file_path = os.path.join(abs_output_dir, f"report_email_{safe_email}.txt")
                    with open(report_file_path, "w", encoding="utf-8") as out_file:
                        out_file.write(f"ОТЧЕТ ПОИСКА ЦИФРОВОГО СЛЕДА ПО EMAIL: {email}\n")
                        out_file.write("-" * 60 + "\n")
                        for svc in unique_services:
                            out_file.write(f"[+] {svc}\n")
                        out_file.write(recommendations)
                    print(f"\033[92m[+] Текстовый отчёт сохранён: {report_file_path}\033[0m")

                if formats in ["json", "all"]:
                    json_file_path = os.path.join(abs_output_dir, f"report_email_{safe_email}.json")
                    with open(json_file_path, "w", encoding="utf-8") as out_file:
                        json.dump({"email": email, "found_services": unique_services}, out_file, ensure_ascii=False,
                                  indent=4)
                    print(f"\033[92m[+] JSON отчёт сохранён: {json_file_path}\033[0m")

            print(recommendations)

        except Exception as e:
            print(f"\033[91m[!] Ошибка выполнения holehe: {e}\033[0m")

        tor_proc.terminate()
        tor_proc.wait()
    else:
        print("\033[91m[!] Tor не найден. Сканирование почты невозможно.\033[0m")