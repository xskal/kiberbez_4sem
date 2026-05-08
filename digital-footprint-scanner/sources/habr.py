import requests

class HabrSource:
    def __init__(self):
        self.name = "Habr"
        # Здесь мы можем сразу внедрить поддержку прокси, о которой говорили
        self.proxies = None # Можно заполнить словарем с прокси

    def search(self, query: str, search_type: str) -> list:
        # Habr актуален только для поиска по никнейму
        if search_type != "username":
            return []

        results = []
        url = f"https://habr.com/users/{query}/"
        
        try:
            # Делаем запрос, имитируя браузер через headers
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, proxies=self.proxies, timeout=5)

            if response.status_code == 200:
                results.append({
                    "source": self.name,
                    "type": "profile",
                    "url": url,
                    "description": f"Найден активный профиль пользователя на Habr: {query}",
                    "risk_level": "medium" # Наличие профиля повышает риск деанона
                })
        except Exception as e:
            results.append({
                "source": self.name,
                "type": "error",
                "description": f"Ошибка при проверке Habr: {str(e)}"
            })
        
        return results
