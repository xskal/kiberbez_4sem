import phonenumbers
from phonenumbers import geocoder, carrier, phonenumberutil
import os, re, urllib.parse
from datetime import datetime
from bs4 import BeautifulSoup
from curl_cffi import requests as cffi

C = {"B": "\033[1m", "R": "\033[0m", "RED": "\033[91m", "GR": "\033[92m", "Y": "\033[93m", "BL": "\033[94m",
     "C": "\033[96m", "D": "\033[2m"}
SEP = f"{C['D']}{'─' * 55}{C['R']}"


def _get(url, **kwargs):
    try:
        return cffi.get(url, impersonate="chrome110", timeout=10, **kwargs)
    except:
        return None


def check_reputation(raw: str) -> list:
    results = []
    r1 = _get(f"https://ktozvonil.net/nomer/{raw}/")
    if r1 and any(w in r1.text.lower() for w in ['мошен', 'спам', 'реклам', 'коллектор']):
        results.append("KtoZvonil: ⚠️ Негативный рейтинг (Спам/Мошенники)")

    r2 = _get(f"https://www.shouldianswer.net/phone-number/8{raw[1:]}")
    if r2:
        score = BeautifulSoup(r2.text, 'html.parser').find('div', class_='score')
        if score and score.text.strip(): results.append(f"ShouldIAnswer: ℹ️ {score.text.strip()}")

    return results if results else ["Базы чисты: явного негатива не найдено"]


def check_tg(raw: str) -> str:
    r = _get(f"https://t.me/+{raw}")
    if not r: return "❔ Недоступно (Возможно нужен VPN)"

    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.find("meta", property="og:title")
    name = title.get("content", "") if title else ""

    if not name or any(x in name for x in ["Chat with", "Share on", "Join group", "Telegram"]):
        return "❔ Скрыто настройками или аккаунта нет"
    return f"✅ Найдено имя: {name}"


def ddg_dorks(query: str, validate_digits: str) -> list:
    snippets = []
    r = _get(f"https://html.duckduckgo.com/html/?q={urllib.parse.quote_plus(query)}")
    if r:
        for a in BeautifulSoup(r.text, "html.parser").find_all("a", class_="result__snippet")[:3]:
            text = a.text.strip().replace("\n", " ")
            if validate_digits in re.sub(r'\D', '', text):
                snippets.append(text)
    return snippets


def run_phone_logic(phone: str, output_dir: str = "reports"):
    try:
        p = phonenumbers.parse(phone, "RU")
        if not phonenumbers.is_valid_number(p):
            return print(f"{C['RED']}[!] Номер невалиден!{C['R']}")

        m = {
            "e164": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164),
            "intl": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.INTERNATIONAL),
            "nat": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.NATIONAL),
            "raw": phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)[1:],
            "reg": geocoder.description_for_number(p, "ru") or "Неизвестно",
            "op": carrier.name_for_number(p, "ru") or "Определяется по MNP",
            "is_toll": phonenumberutil.number_type(p) == phonenumberutil.PhoneNumberType.TOLL_FREE,
            "is_mob": str(p.country_code) == "7" and str(p.national_number)[0] == "9"
        }
        loc_digits = m['raw'][1:] if m['raw'].startswith("7") else m['raw']

        sigs = [m['e164'], m['intl'], m['nat'], m['raw'], f"8{loc_digits}"]

        print(f"\n{C['B']}{C['C']}╔══ PHONE OSINT :: {m['intl']} ══╗{C['R']}\n")

        print(f"{C['BL']}{C['B']}[*] МЕТАДАННЫЕ НОМЕРА{C['R']}\n{SEP}")
        print(f"  ├─ Регион   : {m['reg']}\n  ├─ Оператор : {m['op']}")
        print(
            f"  └─ Тип      : {'Бесплатный 8-800' if m['is_toll'] else ('Мобильный 📱' if m['is_mob'] else 'Стационарный ☎️')}")

        print(f"\n{C['Y']}{C['B']}[*] РЕПУТАЦИЯ{C['R']}\n{SEP}")
        if m['is_toll']:
            rep = ["Коммерческая линия. Базы спама не проверяются."]
        else:
            rep = check_reputation(m['raw'])
        for r in rep: print(f"  · {r}")

        tg_link, wa_link = f"https://t.me/+{m['raw']}", f"https://wa.me/{m['raw']}"
        print(f"\n{C['BL']}{C['B']}[*] МЕССЕНДЖЕРЫ{C['R']}\n{SEP}")

        tg_status = "❌ Пропуск: стационарный номер"
        wa_status = "❌ Пропуск: стационарный номер"
        if m['is_mob']:
            tg_status = check_tg(m['raw'])
            wa_status = "❔ Откройте ссылку для проверки чата"
            print(f"  Telegram : {tg_status}\n             {C['D']}└─ {tg_link}{C['R']}")
            print(f"  WhatsApp : {wa_status}\n             {C['D']}└─ {wa_link}{C['R']}")
        else:
            print(f"  Telegram : {tg_status}")
            print(f"  WhatsApp : {wa_status}")

        print(f"\n{C['Y']}{C['B']}[*] OSINT — ПОИСКОВЫЕ ИНДЕКСЫ{C['R']}\n{SEP}")
        dorks_data = {}
        if not m['is_toll']:
            queries = {
                "Объявления / Форумы": f'"{m["e164"]}" OR "{m["nat"]}"',
                "Документы (PDF/XLS)": f'"{m["raw"]}" filetype:pdf OR filetype:xlsx OR filetype:docx',
                "IT Утечки (Pastebin/GitHub)": f'site:pastebin.com OR site:github.com "{m["raw"]}"'
            }
            for name, q in queries.items():
                snippets = ddg_dorks(q, loc_digits)
                if snippets: dorks_data[name] = {"url": f"https://www.google.com/search?q={urllib.parse.quote_plus(q)}",
                                                 "snips": snippets}

            if not dorks_data:
                print(f"  {C['GR']}✅ Публичных упоминаний и документов не обнаружено.{C['R']}")
            else:
                for name, data in dorks_data.items():
                    print(f"\n  {C['RED']}⚠️  {name}{C['R']}\n     {C['D']}Google: {data['url']}{C['R']}")
                    for s in data['snips']: print(f"     {C['D']}> «{s[:120]}»{C['R']}")
        else:
            print(f"  Найти компанию: https://www.google.com/search?q={urllib.parse.quote_plus(m['nat'])}")

        print(f"\n{C['C']}{C['B']}[*] PIVOT — СЛЕДУЮЩИЕ ШАГИ{C['R']}\n{SEP}")
        print(f"  → Поиск ВК: https://vk.com/search?c[section]=people&c[phone]={m['raw']}")
        print(f"  → Поиск в Google: https://www.google.com/search?q={urllib.parse.quote_plus(m['nat'])}")
        print(f"  → Telegram Бот: https://t.me/getcontact_bot\n  → NumBuster: https://numbuster.com/number/{m['raw']}")

        os.makedirs(output_dir, exist_ok=True)
        rep_path = os.path.join(output_dir, f"phone_osint_{m['raw']}.txt")
        with open(rep_path, "w", encoding="utf-8") as f:
            f.write(f"╔{'═' * 53}╗\n")
            f.write(f"║ OSINT REPORT: {m['intl']:<37} ║\n")
            f.write(f"║ GENERATED: {datetime.now().strftime('%Y-%m-%d %H:%M'):<40} ║\n")
            f.write(f"╚{'═' * 53}╝\n\n")

            f.write("[ МЕТАДАННЫЕ ]\n")
            f.write(f" • Регион   : {m['reg']}\n")
            f.write(f" • Оператор : {m['op']}\n")
            f.write(
                f" • Тип связи: {'Бесплатный 8-800' if m['is_toll'] else ('Мобильный' if m['is_mob'] else 'Стационарный')}\n\n")

            f.write("[ ПОИСКОВЫЕ СИГНАТУРЫ ]\n")
            for s in sigs: f.write(f" • {s}\n")
            f.write("\n")

            f.write("[ РЕПУТАЦИЯ И СПАМ-БАЗЫ ]\n")
            for r in rep: f.write(f" • {r}\n")
            f.write("\n")

            f.write("[ МЕССЕНДЖЕРЫ И СОЦСЕТИ ]\n")
            f.write(f" • Telegram : {tg_status}\n")
            if m['is_mob']: f.write(f"   Ссылка   : {tg_link}\n")
            f.write(f" • WhatsApp : {wa_status}\n")
            if m['is_mob']: f.write(f"   Ссылка   : {wa_link}\n")
            f.write("\n")

            f.write("[ УТЕЧКИ И УПОМИНАНИЯ (DORKS) ]\n")
            if not dorks_data:
                f.write(" • Публичных упоминаний, баз данных и документов не обнаружено.\n")
            else:
                for name, data in dorks_data.items():
                    f.write(f" ⚠️ {name}:\n")
                    f.write(f"   Поиск: {data['url']}\n")
                    for snip in data['snips']:
                        f.write(f"   > \"{snip[:120]}...\"\n")
            f.write("\n")

            f.write("[ PIVOT (ВЕКТОРЫ ДЛЯ РУЧНОГО ПОИСКА) ]\n")
            f.write(f" • VKontakte: https://vk.com/search?c[section]=people&c[phone]={m['raw']}\n")
            f.write(f" • Google: https://www.google.com/search?q={urllib.parse.quote_plus(m['nat'])}\n")
            f.write(f" • GetContact: https://t.me/getcontact_bot\n")
            f.write(f" • NumBuster: https://numbuster.com/number/{m['raw']}\n")

        print(f"\n{C['Y']}[!] Отчёт сохранён: {rep_path}{C['R']}\n")

    except Exception as e:
        print(f"{C['RED']}[!] Системная ошибка: {e}{C['R']}")
