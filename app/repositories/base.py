"""Базовый абстрактный репозиторий для работы с сущностями БД.

Паттерн «Репозиторий» изолирует бизнес-логику от деталей хранения данных:
UI знает только об интерфейсе репозитория, но не об SQL или psycopg2.
"""

from abc import ABC, abstractmethod
from typing import Optional


class BaseRepository(ABC):
    """Абстрактный базовый класс репозитория.

    Определяет стандартный CRUD-интерфейс для всех сущностей приложения.
    Каждый конкретный репозиторий обязан реализовать все пять методов.
    """

    @abstractmethod
    def get_all(self) -> list:
        """Возвращает список всех записей данной сущности из БД."""

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[object]:
        """Возвращает одну запись по первичному ключу или None, если не найдена."""

    @abstractmethod
    def create(self, entity: object) -> object:
        """Вставляет новую запись в БД и возвращает её с присвоенным id."""

    @abstractmethod
    def update(self, entity: object) -> object:
        """Обновляет существующую запись в БД и возвращает обновлённый объект."""

    @abstractmethod
    def delete(self, id: int) -> bool:
        """Удаляет запись по первичному ключу. Возвращает True при успехе."""
