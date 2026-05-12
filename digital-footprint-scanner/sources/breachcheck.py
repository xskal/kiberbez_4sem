"""Проверка утечек (имитация)."""

import hashlib
from sources.base import BaseSource


class BreachCheckSource(BaseSource):
    """Источник: Проверка утечек (имитация)."""
    
    def __init__(self):
        super().__init__("BreachCheck")
    
    def search(self, query: str, search_type: str) -> list:
        self.results = []
        
        if search_type == "email":
            hash_val = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
            breach_count = hash_val % 4
            
            if breach_count > 0:
                self.results.append({
                    "source": self.name,
                    "type": "breach",
                    "url": "https://haveibeenpwned.com",
                    "description": f"⚠️ Email найден в {breach_count} утечках! Рекомендуется сменить пароль.",
                    "risk_level": "high"
                })
            else:
                self.results.append({
                    "source": self.name,
                    "type": "info",
                    "url": "",
                    "description": "Email не найден в известных утечках"
                })
        
        elif search_type == "username":
            self.results.append({
                "source": self.name,
                "type": "info",
                "url": "",
                "description": "Проверка утечек для username: доступно в платной версии API"
            })
        
        else:
            self.results.append({
                "source": self.name,
                "type": "info",
                "url": "",
                "description": "Проверка утечек для номера телефона: доступно в платной версии API"
            })
        
        return self.results