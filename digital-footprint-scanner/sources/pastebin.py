"""Поиск по Pastebin (имитация, так как API требует ключа)."""

import hashlib
from sources.base import BaseSource


class PastebinSource(BaseSource):
    """Источник: Pastebin (имитация)."""
    
    def __init__(self):
        super().__init__("Pastebin")
    
    def search(self, query: str, search_type: str) -> list:
        self.results = []
        
        if search_type in ["username", "email"]:
            hash_val = int(hashlib.md5(query.encode()).hexdigest()[:8], 16)
            found = hash_val % 2 == 0
            
            if found:
                self.results.append({
                    "source": self.name,
                    "type": "paste",
                    "url": f"https://pastebin.com/example_{hash_val % 1000}",
                    "description": f"Найдено упоминание '{query}' в публичной пасте"
                })
            else:
                self.results.append({
                    "source": self.name,
                    "type": "info",
                    "url": "",
                    "description": "Упоминаний не найдено"
                })
        else:
            self.results.append({
                "source": self.name,
                "type": "info",
                "url": "",
                "description": "Pastebin не специализируется на поиске по телефону"
            })
        
        return self.results