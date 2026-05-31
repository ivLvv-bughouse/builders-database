"""Модель объекта недвижимости (квартира, паркоместо, коммерческое)."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Property:
    """Объект недвижимости в конкретном здании.

    Поля соответствуют столбцам таблицы properties в базе данных.
    property_type ∈ {'квартира', 'паркоместо', 'коммерческое'}
    status        ∈ {'свободен', 'забронирован', 'продан'}
    """

    property_type: str
    number: str
    area: Decimal
    price: Decimal
    status: str
    building_id: int
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Property":
        """Создаёт объект Property из строки результата psycopg2-запроса.

        Порядок полей: id, property_type, number, area, price, status, building_id.
        """
        return cls(
            id=row[0],
            property_type=row[1],
            number=row[2],
            area=row[3],
            price=row[4],
            status=row[5],
            building_id=row[6],
        )
