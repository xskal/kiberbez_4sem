import phonenumbers
from phonenumbers import geocoder, carrier, timezone, phonenumberutil
import os
import requests
from bs4 import BeautifulSoup
import urllib.parse
import json


def check_reputation(check_number):
    url = f"https://www.neberitrubku.ru/nomer-telefona/{check_number}"
    tags = []

    flare_url = "http://localhost:8191/v1"
    payload = {
        "cmd": "request.get",
        "url": url,
        "maxTimeout": 60000
    }

    try:
        response = requests.post(flare_url, headers={"Content-Type": "application/json"}, json=payload, timeout=65)

        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "ok":
                html = result["solution"]["response"]
                soup = BeautifulSoup(html, 'html.parser')

                desc = soup.find('meta', attrs={'name': 'description'})
                if desc and desc.get('content'):
                    tags.append(desc.get('content').split('.')[0])

                categories = soup.find_all('div', class_='score')
                for cat in categories:
                    text = cat.text.strip()
                    if text and text not in tags:
                        tags.append(text)
            else:
                return ["Cloudflare не пробит: сайт требует сложную капчу"]
        else:
            return [f"Ошибка FlareSolverr: {response.status_code}"]

    except requests.exceptions.ConnectionError:
        return ["[!] FlareSolverr не запущен! Запусти контейнер в Docker (порт 8191)"]
    except Exception as e:
        return [f"Ошибка парсинга: {e}"]

    return tags if tags else ["Номер чист (отзывов не найдено)"]


def run_phone_logic(phone_number, output_dir="reports"):
    try:
        parsed_number = phonenumbers.parse(phone_number, "RU")
        if not phonenumbers.is_valid_number(parsed_number):
            print("\033[91m[!] Номер невалиден!\033[0m")
            return

        region = geocoder.description_for_number(parsed_number, "ru")
        provider = carrier.name_for_number(parsed_number, "ru")

        num_type = phonenumberutil.number_type(parsed_number)
        is_toll_free = num_type == phonenumberutil.PhoneNumberType.TOLL_FREE

        if is_toll_free:
            region = "Федеральный номер (РФ)"
            provider = "Горячая линия (8-800)"

        f_e164 = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
        f_intl = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.INTERNATIONAL)
        f_nat = phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.NATIONAL)
        raw_digits = f_e164.replace("+", "")

        is_mobile = str(parsed_number.country_code) == '7' and str(parsed_number.national_number)[0] == '9'

        print(f"\n\033[1;94m[ ANALYZING: {f_intl} ]\033[0m")
        print(f"\033[92m[+] Метаданные:\033[0m")
        print(f"    ├─ Регион: {region if region else 'Неизвестно'}")
        print(f"    ├─ Оператор: {provider if provider else 'Определяется по MNP'}")
        print(
            f"    └─ Тип связи: {'Мобильный' if is_mobile else ('Бесплатный вызов (Toll-Free)' if is_toll_free else 'Стационарный/Unknown')}")

        print(f"\n\033[92m[+] Генерация поисковых сигнатур:\033[0m")
        search_formats = [
            f_e164,
            f_nat,
            raw_digits[1:],
            f"{raw_digits[1:4]}-{raw_digits[4:7]}-{raw_digits[7:9]}-{raw_digits[9:]}"
        ]
        for fmt in search_formats:
            print(f"    - Signature: {fmt}")

        print(f"\n\033[93m[*] Проверка репутации:\033[0m")

        check_number = f"8{raw_digits[1:]}"

        if is_toll_free:
            rep_tags = ["Это коммерческая горячая линия. Отзывы не собираются."]
            for tag in rep_tags:
                print(f"    - {tag}")
        else:
            rep_tags = check_reputation(check_number)
            for tag in rep_tags:
                print(f"    - {tag}")

        messengers = {
            "Telegram": f"https://t.me/+{raw_digits}",
            "WhatsApp": f"https://wa.me/{raw_digits}",
            "Viber": f"viber://add?number={raw_digits}"
        }

        q_forums = urllib.parse.quote_plus(f'"{f_e164}" OR "{f_nat}"')
        q_docs = urllib.parse.quote_plus(f'"{raw_digits}" filetype:pdf OR filetype:xlsx OR filetype:docx')
        q_leaks = urllib.parse.quote_plus(f'site:pastebin.com OR site:github.com "{raw_digits}"')
        q_getcontact = urllib.parse.quote_plus(f'site:getcontact.com "{raw_digits}"')

        dorks = {
            "Объявления/Форумы": f"https://www.google.com/search?q={q_forums}",
            "Поиск документов (PDF/XLS)": f"https://www.google.com/search?q={q_docs}",
            "Поиск в Pastebin/Leaks": f"https://www.google.com/search?q={q_leaks}"
        }

        checkers = {
            "GetContact": f"https://www.google.com/search?q={q_getcontact}",
            "TrueCaller": f"https://www.truecaller.com/search/ru/{raw_digits}",
            "Spam Check": f"https://www.neberitrubku.ru/nomer-telefona/{check_number}"
        }

        print(f"\n\033[94m[*] Поиск связок:\033[0m")
        print(f"    - Искать номер как ник: --username {raw_digits}")

        print(f"\n\033[94m[*] Прямые переходы:\033[0m")
        for k, v in messengers.items(): print(f"    - {k}: {v}")

        if not is_toll_free:
            print(f"\n\033[94m[*] Глубокий поиск утечек:\033[0m")
            for k, v in dorks.items(): print(f"    - {k}: {v}")
        else:
            print(f"\n\033[94m[*] Базовый поиск:\033[0m")
            print(f"    - Искать компанию: https://www.google.com/search?q={urllib.parse.quote_plus(f_nat)}")

        report_path = os.path.join(output_dir, f"phone_full_{raw_digits}.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(f"OSINT REPORT FOR: {f_intl}\n{'=' * 30}\n")
            f.write(f"Region: {region}\nCarrier: {provider}\nType: {'Mobile' if is_mobile else 'Unknown'}\n\n")
            f.write("[ REPUTATION TAGS ]\n" + "\n".join(rep_tags) + "\n\n")
            f.write("[ SIGNATURES ]\n" + "\n".join(search_formats) + "\n\n")
            f.write("[ LINKS ]\n")
            for k, v in messengers.items(): f.write(f"{k}: {v}\n")
            if not is_toll_free:
                for k, v in dorks.items(): f.write(f"{k}: {v}\n")
            for k, v in checkers.items(): f.write(f"{k}: {v}\n")

        print(f"\n\033[93m[!] Полный аналитический отчет: {report_path}\033[0m")

    except Exception as e:
        print(f"\033[91m[!] Ошибка анализа: {e}\033[0m")