import phonenumbers
from phonenumbers import geocoder, carrier, phonenumberutil
import os, re, urllib.parse, sys, json
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi

C_BLUE = "\033[94m"
C_GREEN = "\033[92m"
C_YELLOW = "\033[93m"
C_RED = "\033[91m"
C_RESET = "\033[0m"

def _get(url, **kwargs):
    try:
        return cffi.get(url, impersonate="chrome110", timeout=10, **kwargs)
    except:
        return None

def get_dadata_info(phone: str) -> dict:
    api_key = os.getenv("DADATA_API_KEY", "")
    secret_key = os.getenv("DADATA_SECRET_KEY", "")

    if not api_key or not secret_key:
        print(f"{C_YELLOW}[!] Ключи DaData не найдены ни в коде, ни в системе. Определение города пропущено.{C_RESET}")
        return {}

    try:
        url = "https://cleaner.dadata.ru/api/v1/clean/phone"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Token {api_key}",
            "X-Secret": secret_key
        }
        r = cffi.post(url, json=[phone], headers=headers, impersonate="chrome110", timeout=10)
        if r.status_code == 200:
            data = r.json()[0]
            return {
                "region": data.get("region_with_type") or data.get("region", ""),
                "city": data.get("city_with_type") or data.get("city", ""),
                "provider": data.get("provider", "")
            }
    except Exception as e:
        print(f"{C_RED}[!] Ошибка API DaData: {e}{C_RESET}")
    return {}

def extract_artifacts_from_text(text: str) -> dict:
    artifacts = {
        "emails": [],
        "dates": [],
        "other_phones": []
    }

    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    found_emails = re.findall(email_pattern, text)
    if found_emails: artifacts["emails"] = list(set(found_emails))

    date_pattern = r'\b(?:\d{2}[./-]\d{2}[./-]\d{4}|\d{4}[./-]\d{2}[./-]\d{2})\b'
    found_dates = re.findall(date_pattern, text)
    if found_dates: artifacts["dates"] = list(set(found_dates))

    phone_pattern = r'\b(?:\(\d{3,4}\)\s*)?\d{2,3}[-\s]\d{2,3}[-\s]\d{2,3}\b'
    raw_phones = re.findall(phone_pattern, text)
    valid_phones = [p for p in raw_phones if len(re.sub(r'\D', '', p)) >= 6]
    if valid_phones: artifacts["other_phones"] = list(set(valid_phones))

    return artifacts

def check_reputation(raw: str) -> list:
    results = []

    neb_url = f"https://www.neberitrubku.ru/nomer-telefona/8{raw[1:]}"
    r1 = _get(neb_url)
    if r1:
        soup = BeautifulSoup(r1.text, 'html.parser')
        score = soup.find('div', class_='score')
        if score and score.text.strip():
            results.append(f"NeberiTrubku: Рейтинг {score.text.strip()} (Пруф: {neb_url})")

    smsbox_url = f"https://mysmsbox.ru/phone-search/{raw}"
    r2 = _get(smsbox_url)
    if r2 and r2.status_code == 200:
        text_lower = r2.text.lower()
        if "мошенник" in text_lower or "спам" in text_lower or "реклама" in text_lower:
            results.append(f"MySmsBox: ⚠️ Возможен спам/негатив (Ручная проверка: {smsbox_url})")

    return results if results else ["Базы чисты: явного негатива не найдено"]

def check_tg(raw: str) -> str:
    r = _get(f"https://t.me/+{raw}")
    if not r: return "Недоступно (Возможно нужен VPN)"

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("meta", property="og:title")
    name = title.get("content", "") if title else ""

    if not name or any(x in name for x in ["Chat with", "Share on", "Join group", "Telegram"]):
        return "Скрыто настройками или аккаунт отсутствует"
    return f"{C_GREEN}Найдено имя: {name}{C_RESET}"

def ddg_dorks(query: str, validate_digits: str) -> list:
    snippets = []
    r = _get(f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}")
    if r:
        for a in BeautifulSoup(r.text, "html.parser").find_all("a", class_="result__snippet")[:3]:
            text = a.text.strip().replace("\n", " ")
            if validate_digits in re.sub(r'\D', '', text):
                snippets.append(text)
    return snippets

def generate_phone_recommendations(m, rep_flags, has_leaks, report_path=None):
    rec_text = []
    rec_text.append("\n" + "=" * 60)
    rec_text.append(" 🛡️ АВТОМАТИЧЕСКИЕ РЕКОМЕНДАЦИИ ПО БЕЗОПАСНОСТИ НОМЕРА")
    rec_text.append("=" * 60)

    if m.get("is_mob"):
        rec_text.append("\n🔴 [КРИТИЧЕСКИЙ РИСК] Определен мобильный номер.")
        rec_text.append("  ↳ Угроза: Вероятна привязка к банковским сервисам, Госуслугам и соцсетям.")
        rec_text.append("  ↳ Рекомендация: Скрыть видимость номера в Telegram и WhatsApp для всех, кроме контактов.")
        rec_text.append("  ↳               Завести виртуальный номер для регистраций на досках объявлений.")

    if any("спам" in r.lower() or "мошенник" in r.lower() for r in rep_flags):
        rec_text.append("\n🟡 [СРЕДНИЙ РИСК] Номер зафиксирован в антиспам-базах.")
        rec_text.append("  ↳ Угроза: Повышенный риск таргетированного фишинга и спам-прозвонов.")
        rec_text.append("  ↳ Рекомендация: Включить системную блокировку неизвестных спам-номеров.")

    if has_leaks:
        rec_text.append("\n🔴 [КРИТИЧЕСКИЙ РИСК] Найдены прямые упоминания в поисковых индексах.")
        rec_text.append("  ↳ Угроза: Возможна связь номера с ФИО, email или адресом (деанонимизация).")
        rec_text.append("  ↳ Рекомендация: Провести зачистку старых аккаунтов, запросить удаление данных из кэша поисковиков.")

    if not m.get("is_mob") and not has_leaks:
        rec_text.append("\n🟢 [НИЗКИЙ РИСК] Корпоративный или стационарный номер без критичных утечек.")
        rec_text.append("  ↳ Уровень угрозы: Минимальный.")

    rec_text.append("\n" + "=" * 60 + "\n")

    final_output = "\n".join(rec_text)
    print(final_output)

    if report_path and os.path.exists(report_path):
        try:
            with open(report_path, "a", encoding="utf-8") as f:
                f.write(final_output)
        except Exception:
            pass

def run_phone_logic(phone: str, formats: str = "txt", output_dir: str = "reports"):
    try:
        p = phonenumbers.parse(phone, "RU")
        if not phonenumbers.is_valid_number(p):
            print(f"{C_RED}[!] Номер невалиден!{C_RESET}")
            return

        raw_num = phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)[1:]
        dadata_data = get_dadata_info(raw_num)

        m = {
            "e164": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164),
            "intl": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "nat": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.NATIONAL),
            "raw": raw_num,
            "reg": dadata_data.get("region") or geocoder.description_for_number(p, "ru") or "Россия",
            "city": dadata_data.get("city") or "Не определен",
            "op": dadata_data.get("provider") or carrier.name_for_number(p, "ru") or "Определяется по MNP",
            "is_toll": phonenumberutil.number_type(p) == phonenumberutil.PhoneNumberType.TOLL_FREE,
            "is_mob": str(p.country_code) == "7" and str(p.national_number)[0] == "9"
        }
        loc_digits = m['raw'][1:] if m['raw'].startswith("7") else m['raw']

        print(f"\n{C_BLUE}[*] Запуск OSINT сканирования номера {m['intl']}...{C_RESET}")

        print(f"\n{C_BLUE}[1/4] Анализ метаданных номера...{C_RESET}")
        print(f"  ├─ Страна/Регион: {m['reg']}")
        print(f"  ├─ Город        : {m['city']}")
        print(f"  ├─ Оператор     : {m['op']}")
        print(f"  └─ Тип          : {'Бесплатный 8-800' if m['is_toll'] else ('Мобильный' if m['is_mob'] else 'Стационарный')}")

        print(f"\n{C_BLUE}[2/4] Проверка по базам спама и мошенников...{C_RESET}")
        if m['is_toll']:
            rep = ["Коммерческая линия. Базы спама не проверяются."]
        else:
            rep = check_reputation(m['raw'])
        for r in rep:
            print(f"  └─ {r}")

        print(f"\n{C_BLUE}[3/4] Проверка привязки к мессенджерам...{C_RESET}")
        tg_status = "Пропуск: стационарный номер"
        wa_status = "Пропуск: стационарный номер"
        if m['is_mob']:
            tg_status = check_tg(m['raw'])
            wa_status = "Требуется ручная проверка по ссылке"
            print(f"  ├─ Telegram : {tg_status}")
            print(f"  └─ WhatsApp : {wa_status} (https://wa.me/{m['raw']})")
        else:
            print(f"  ├─ Telegram : {tg_status}")
            print(f"  └─ WhatsApp : {wa_status}")

        print(f"\n{C_BLUE}[4/4] Поиск по поисковым индексам и доскам объявлений (Dorks)...{C_RESET}")
        dorks_data = {}
        all_extracted_emails = set()
        all_extracted_dates = set()
        all_extracted_phones = set()
        has_dork_leaks = False

        if not m['is_toll']:
            queries = {
                "Avito (Кэш)": f'site:avito.ru "{m["raw"]}" OR "{m["nat"]}"',
                "Объявления / Форумы": f'"{m["e164"]}" OR "{m["nat"]}"',
                "Документы (PDF/XLS)": f'"{m["raw"]}" filetype:pdf OR filetype:xlsx',
                "Утечки (Pastebin/GitHub)": f'site:pastebin.com OR site:github.com "{m["raw"]}"'
            }
            for name, q in queries.items():
                snippets = ddg_dorks(q, loc_digits)
                if snippets:
                    dorks_data[name] = {
                        "url": f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}",
                        "snips": snippets
                    }
                    has_dork_leaks = True

            if not dorks_data:
                print(f"  └─ {C_GREEN}Публичных упоминаний и документов не обнаружено.{C_RESET}")
            else:
                for name, data in dorks_data.items():
                    print(f"  ├─ {C_YELLOW}Найдено в категории: {name}{C_RESET}")
                    print(f"  │  Ссылка: {data['url']}")
                    for s in data['snips']:
                        print(f"  │  > {s[:100]}...")
                        extracted = extract_artifacts_from_text(s)
                        all_extracted_emails.update(extracted["emails"])
                        all_extracted_dates.update(extracted["dates"])
                        all_extracted_phones.update(extracted["other_phones"])

                if all_extracted_emails or all_extracted_phones or all_extracted_dates:
                    print(f"  │")
                    print(f"  ├─ {C_BLUE}[*] Автоматически извлеченные артефакты из текстов:{C_RESET}")
                    if all_extracted_emails: print(f"  │  ├─ Emails: {', '.join(all_extracted_emails)}")
                    if all_extracted_phones: print(f"  │  ├─ Другие номера: {', '.join(all_extracted_phones)}")
                    if all_extracted_dates:  print(f"  │  └─ Даты: {', '.join(all_extracted_dates)}")

        else:
            print(f"  └─ Найти компанию: https://www.google.com/search?q={urllib.parse.quote_plus(m['nat'])}")

        print(f"\n{C_YELLOW}[*] Векторы для ручного поиска (Pivot):{C_RESET}")
        print(f"  → VK: https://vk.com/search?c[section]=people&c[phone]={m['raw']}")
        print(f"  → GetContact: https://t.me/getcontact_bot")

        rep_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            base_filename = f"phone_osint_{m['raw']}"

            json_data = {
                "metadata": m,
                "reputation": rep,
                "messengers": {
                    "telegram": tg_status,
                    "whatsapp": wa_status,
                    "whatsapp_link": f"https://wa.me/{m['raw']}"
                },
                "dorks": dorks_data,
                "extracted_artifacts": {
                    "emails": list(all_extracted_emails),
                    "phones": list(all_extracted_phones),
                    "dates": list(all_extracted_dates)
                },
                "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M')
            }

            if formats in ["txt", "all"]:
                rep_path = os.path.join(output_dir, f"{base_filename}.txt")
                with open(rep_path, "w", encoding="utf-8") as f:
                    f.write(f"OSINT REPORT: {m['intl']}\n")
                    f.write(f"GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
                    f.write("-" * 40 + "\n\n")

                    f.write("[ МЕТАДАННЫЕ ]\n")
                    f.write(f"Страна/Регион: {m['reg']}\nГород: {m['city']}\nОператор: {m['op']}\nТип: {'Бесплатный 8-800' if m['is_toll'] else ('Мобильный' if m['is_mob'] else 'Стационарный')}\n\n")

                    f.write("[ РЕПУТАЦИЯ ]\n")
                    for r in rep: f.write(f"- {r}\n")
                    f.write("\n")

                    f.write("[ МЕССЕНДЖЕРЫ ]\n")
                    f.write(f"Telegram: {tg_status}\nWhatsApp: {wa_status} (https://wa.me/{m['raw']})\n\n")

                    f.write("[ УТЕЧКИ И УПОМИНАНИЯ (DORKS) ]\n")
                    if not dorks_data:
                        f.write("Ничего не найдено.\n")
                    else:
                        for name, data in dorks_data.items():
                            f.write(f"{name}:\nПоиск: {data['url']}\n")
                            for snip in data['snips']: f.write(f"> {snip[:100]}...\n")

                        if all_extracted_emails or all_extracted_phones or all_extracted_dates:
                            f.write("\n[ ИЗВЛЕЧЕННЫЕ АРТЕФАКТЫ ]\n")
                            if all_extracted_emails: f.write(f"Emails: {', '.join(all_extracted_emails)}\n")
                            if all_extracted_phones: f.write(f"Связанные номера: {', '.join(all_extracted_phones)}\n")
                            if all_extracted_dates: f.write(f"Даты: {', '.join(all_extracted_dates)}\n")
                    f.write("\n")
                print(f"\n{C_GREEN}[+] Текстовый отчёт сохранён: {rep_path}{C_RESET}")

            if formats in ["json", "all"]:
                json_path = os.path.join(output_dir, f"{base_filename}.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(json_data, f, ensure_ascii=False, indent=4)
                print(f"{C_GREEN}[+] JSON отчёт сохранён: {json_path}{C_RESET}")

                if formats == "json":
                    rep_path = json_path

        generate_phone_recommendations(m, rep, has_dork_leaks, report_path=rep_path)

    except Exception as e:
        print(f"{C_RED}[!] Системная ошибка: {e}{C_RESET}")