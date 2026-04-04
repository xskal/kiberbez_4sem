#!/usr/bin/env python3
"""
Автоматизированное средство поиска цифрового следа в сети Интернет.
Прототип версии.
"""

import argparse
import json
import os
import sys
from datetime import datetime

from sources import GitHubSource, PastebinSource, BreachCheckSource


class DigitalFootprintScanner:
    """Основной класс сканера цифрового следа."""
    
    def __init__(self):
        self.sources = []
        self._init_sources()
        self.results = []
        self.query = ""
        self.search_type = ""
    
    def _init_sources(self):
        """Инициализация всех источников."""
        self.sources = [
            GitHubSource(),
            PastebinSource(),
            BreachCheckSource(),
        ]
    
    def scan(self, query: str, search_type: str) -> list:
        """Выполнить сканирование по всем источникам."""
        self.query = query
        self.search_type = search_type
        self.results = []
        
        print(f"\n🔍 Начинаю поиск цифрового следа...")
        print(f"📝 Объект: {query}")
        print(f"📋 Тип: {search_type}")
        print(f"📡 Источников: {len(self.sources)}")
        print("-" * 50)
        
        for source in self.sources:
            print(f"🔎 Проверка {source.name}...")
            try:
                source_results = source.search(query, search_type)
                self.results.extend(source_results)
                for result in source_results:
                    if result.get("type") == "error":
                        print(f"   ⚠️ Ошибка: {result['description']}")
                    elif result.get("risk_level") == "high":
                        print(f"   🔴 {result['description']}")
                    elif result["type"] != "info":
                        print(f"   ✅ Найдено: {result['description']}")
                print(f"   ✓ Готово")
            except Exception as e:
                print(f"   ❌ Ошибка: {str(e)}")
        
        print("-" * 50)
        found_count = len([r for r in self.results if r['type'] not in ['info', 'error']])
        print(f"✅ Сканирование завершено. Найдено результатов: {found_count}")
        
        return self.results
    
    def get_risk_level(self) -> str:
        """Оценить общий уровень риска."""
        high_risk_found = False
        medium_risk_found = False
        
        for result in self.results:
            if result.get("risk_level") == "high":
                high_risk_found = True
            elif result.get("type") == "breach":
                high_risk_found = True
            elif result.get("type") == "paste":
                medium_risk_found = True
            elif result.get("type") == "profile":
                medium_risk_found = True
        
        if high_risk_found:
            return "high"
        elif medium_risk_found:
            return "medium"
        elif len(self.results) > 0:
            return "low"
        else:
            return "unknown"
    
    def get_recommendations(self) -> list:
        """Сформировать рекомендации на основе результатов."""
        recommendations = []
        
        for result in self.results:
            if result.get("type") == "breach":
                recommendations.append("🔐 Смените пароль для этого email и всех связанных аккаунтов")
                recommendations.append("🛡️ Используйте уникальные пароли для каждого сервиса")
                recommendations.append("🔑 Включите двухфакторную аутентификацию где это возможно")
                break
        
        profiles_found = [r for r in self.results if r.get("type") == "profile"]
        if profiles_found:
            recommendations.append("👤 Найдены ваши профили в социальных сетях и сервисах")
            recommendations.append("⚙️ Проверьте настройки приватности: ограничьте видимость личной информации")
        
        pastes_found = [r for r in self.results if r.get("type") == "paste"]
        if pastes_found:
            recommendations.append("📋 Ваши данные найдены в публичных пастах")
            recommendations.append("🗑️ Если возможно, запросите удаление этих данных")
        
        if not recommendations:
            recommendations.append("✅ Ваш цифровой след выглядит чистым. Продолжайте следить за своей конфиденциальностью!")
        
        recommendations.append("🌐 Старайтесь минимизировать публикацию личной информации в интернете")
        
        return recommendations
    
    def save_report_txt(self, filename: str) -> None:
        """Сохранить отчет в TXT формате."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write("ОТЧЕТ ПО РЕЗУЛЬТАТАМ ПОИСКА ЦИФРОВОГО СЛЕДА\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"Объект поиска: {self.query}\n")
            f.write(f"Тип объекта: {self.search_type}\n")
            f.write(f"Дата сканирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Уровень риска: {self.get_risk_level().upper()}\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("НАЙДЕННЫЕ ДАННЫЕ\n")
            f.write("-" * 60 + "\n\n")
            
            found_items = [r for r in self.results if r['type'] not in ['info', 'error']]
            if found_items:
                for i, result in enumerate(found_items, 1):
                    f.write(f"{i}. Источник: {result['source']}\n")
                    f.write(f"   Тип: {result['type']}\n")
                    if result.get('url'):
                        f.write(f"   URL: {result['url']}\n")
                    f.write(f"   Описание: {result['description']}\n\n")
            else:
                f.write("Ничего не найдено.\n\n")
            
            f.write("-" * 60 + "\n")
            f.write("РЕКОМЕНДАЦИИ\n")
            f.write("-" * 60 + "\n\n")
            
            for rec in self.get_recommendations():
                f.write(f"• {rec}\n")
            
            f.write("\n" + "=" * 60 + "\n")
            f.write("Конец отчета\n")
        
        print(f"📄 TXT-отчет сохранен: {filename}")
    
    def save_report_json(self, filename: str) -> None:
        """Сохранить отчет в JSON формате."""
        report = {
            "scan_info": {
                "query": self.query,
                "type": self.search_type,
                "timestamp": datetime.now().isoformat(),
                "risk_level": self.get_risk_level()
            },
            "results": self.results,
            "recommendations": self.get_recommendations()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"📄 JSON-отчет сохранен: {filename}")
    
    def save_report_csv(self, filename: str) -> None:
        """Сохранить отчет в CSV формате."""
        import csv
        
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Источник', 'Тип', 'URL', 'Описание'])
            
            for result in self.results:
                if result['type'] not in ['info', 'error']:
                    writer.writerow([
                        result['source'],
                        result['type'],
                        result.get('url', ''),
                        result['description']
                    ])
        
        print(f"📄 CSV-отчет сохранен: {filename}")
    
    def print_results(self) -> None:
        """Вывести результаты в консоль."""
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТЫ ПОИСКА")
        print("=" * 60)
        
        found_items = [r for r in self.results if r['type'] not in ['info', 'error']]
        
        if found_items:
            print("\n📌 Найденные данные:")
            for result in found_items:
                print(f"\n   📍 {result['source']}")
                print(f"      Тип: {result['type']}")
                if result.get('url'):
                    print(f"      Ссылка: {result['url']}")
                print(f"      {result['description']}")
        else:
            print("\n❌ Ничего не найдено.")
        
        print("\n" + "-" * 60)
        print(f"⚠️ УРОВЕНЬ РИСКА: {self.get_risk_level().upper()}")
        print("-" * 60)
        
        print("\n💡 РЕКОМЕНДАЦИИ:")
        for rec in self.get_recommendations():
            print(f"   • {rec}")
        
        print("\n" + "=" * 60)


def main():
    """Главная функция."""
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
    
    # Определяем тип и значение поиска
    if args.username:
        query = args.username
        search_type = "username"
    elif args.email:
        query = args.email
        search_type = "email"
    else:
        query = args.phone
        search_type = "phone"
    
    # Создаем папку для отчетов
    report_dir = "reports"
    if not args.no_save and not os.path.exists(report_dir):
        os.makedirs(report_dir)
    
    # Запускаем сканирование
    scanner = DigitalFootprintScanner()
    scanner.scan(query, search_type)
    
    # Выводим результаты
    scanner.print_results()
    
    # Сохраняем отчет
    if not args.no_save:
        base_name = args.output if args.output else f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if args.format in ["txt", "all"]:
            scanner.save_report_txt(os.path.join(report_dir, f"{base_name}.txt"))
        
        if args.format in ["json", "all"]:
            scanner.save_report_json(os.path.join(report_dir, f"{base_name}.json"))
        
        if args.format in ["csv", "all"]:
            scanner.save_report_csv(os.path.join(report_dir, f"{base_name}.csv"))


if __name__ == "__main__":
    main()