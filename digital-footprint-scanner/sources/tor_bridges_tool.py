import os
import sys


def update_tor_bridges(bridges_string):
    """
    Принимает текстовый блок с мостами WebTunnel (каждый мост с новой строки),
    вычищает старые мосты из torrc.txt и прописывает новые с префиксом 'Bridge '.
    """
    # Определение пути к torrc.txt (с поддержкой PyInstaller)
    if hasattr(sys, '_MEIPASS'):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    torrc_path = os.path.join(base_dir, "bin", "torrc.txt")

    if not os.path.exists(torrc_path):
        print(f"\033[91m[!] Файл конфигурации не найден по пути: {torrc_path}\033[0m")
        return False

    # Читаем текущий файл torrc.txt
    with open(torrc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Очищаем файл от старых мостов (строки, которые начинаются на 'Bridge ')
    clean_lines = [line for line in lines if not line.strip().startswith("Bridge ")]

    # Разбиваем переданный админом блок текста строго по переносам строк (\n)
    raw_lines = bridges_string.split("\n")
    new_bridges_count = 0

    for line in raw_lines:
        clean_bridge = line.strip()

        # Пропускаем пустые строки, если админ случайно нажал Enter в конце
        if not clean_bridge:
            continue

        # Если админ скопировал строку, где уже написано 'Bridge ', убираем дубль
        if clean_bridge.startswith("Bridge "):
            clean_bridge = clean_bridge[7:].strip()

        # Добавляем отформатированную строку моста WebTunnel
        clean_lines.append(f"Bridge {clean_bridge}\n")
        new_bridges_count += 1

    if new_bridges_count == 0:
        print("\033[91m[!] Не найдено ни одной валидной строки моста. Файл не изменен.\033[0m")
        return False

    # Записываем обновленный конфигурационный файл обратно
    with open(torrc_path, "w", encoding="utf-8") as f:
        f.writelines(clean_lines)

    print("\033[92m[+] Конфигурация Tor успешно обновлена!\033[0m")
    print(f"[+] Успешно добавлено мостов WebTunnel: {new_bridges_count}")
    return True