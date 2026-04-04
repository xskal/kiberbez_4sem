"""Поиск по GitHub API."""

import requests
from sources.base import BaseSource


class GitHubSource(BaseSource):
    """Источник: GitHub (поиск пользователей и кода)."""
    
    def __init__(self):
        super().__init__("GitHub")
        self.base_url = "https://api.github.com"
    
    def search(self, query: str, search_type: str) -> list:
        """
        Поиск на GitHub.
        
        Для username: поиск пользователя
        Для email: поиск в коде и коммитах
        Для phone: GitHub не поддерживает поиск по телефону
        """
        self.results = []
        
        if search_type == "username":
            # Поиск пользователя по username
            url = f"{self.base_url}/users/{query}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    user_data = response.json()
                    self.results.append({
                        "source": self.name,
                        "type": "profile",
                        "url": user_data.get("html_url", ""),
                        "description": f"Найден пользователь: {user_data.get('name', query)}",
                        "details": {
                            "repos": user_data.get("public_repos", 0),
                            "followers": user_data.get("followers", 0)
                        }
                    })
                elif response.status_code == 404:
                    # Пользователь не найден — не добавляем ничего
                    pass
            except requests.RequestException as e:
                self.results.append({
                    "source": self.name,
                    "type": "error",
                    "url": "",
                    "description": f"Ошибка при запросе: {str(e)}"
                })
        
        elif search_type == "email":
            # Поиск email в коде GitHub
            url = f"{self.base_url}/search/code"
            params = {"q": query}
            headers = {"Accept": "application/vnd.github.v3+json"}
            try:
                response = requests.get(url, headers=headers, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get("items", [])[:5]  # Ограничим 5 результатами
                    for item in items:
                        self.results.append({
                            "source": self.name,
                            "type": "code",
                            "url": item.get("html_url", ""),
                            "description": f"Email найден в коде: {item.get('repository', {}).get('full_name', '')}"
                        })
                    if not items:
                        self.results.append({
                            "source": self.name,
                            "type": "info",
                            "url": "",
                            "description": "Email не найден в публичном коде"
                        })
            except requests.RequestException as e:
                self.results.append({
                    "source": self.name,
                    "type": "error",
                    "url": "",
                    "description": f"Ошибка при запросе: {str(e)}"
                })
        
        else:  # phone
            self.results.append({
                "source": self.name,
                "type": "info",
                "url": "",
                "description": "GitHub не поддерживает поиск по номеру телефона"
            })
        
        return self.results