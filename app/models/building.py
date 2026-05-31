"""Модель здания строительной компании."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Building:
    """Здание (жилой комплекс или бизнес-центр), в котором расположены объекты.

    Поля соответствуют столбцам таблицы buildings в базе данных.
    """

    name: str
    address: str
    floors: int
    completion_date: date
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Building":
        """Создаёт объект Building из строки результата psycopg2-запроса.

        Порядок полей: id, name, address, floors, completion_date.
        """
        return cls(
            id=row[0],
            name=row[1],
            address=row[2],
            floors=row[3],
            completion_date=row[4],
        )
