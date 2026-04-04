"""Базовый класс для всех источников данных."""

from abc import ABC, abstractmethod


class BaseSource(ABC):
    """Абстрактный базовый класс для источника данных."""
    
    def __init__(self, name: str):
        self.name = name
        self.results = []
    
    @abstractmethod
    def search(self, query: str, search_type: str) -> list:
        """
        Выполнить поиск по источнику.
        
        Args:
            query: Строка поиска (username, email, телефон)
            search_type: Тип поиска ('username', 'email', 'phone')
            
        Returns:
            list: Список найденных результатов
        """
        pass
    
    def get_results(self) -> list:
        """Вернуть результаты поиска."""
        return self.results