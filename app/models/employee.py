"""Модель сотрудника строительной компании."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass
class Employee:
    """Сотрудник компании, оформляющий договоры купли-продажи.

    Поля соответствуют столбцам таблицы employees в базе данных.
    """

    last_name: str
    first_name: str
    position: str
    phone: str
    salary: Decimal
    middle_name: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Employee":
        """Создаёт объект Employee из строки результата psycopg2-запроса.

        Порядок полей: id, last_name, first_name, middle_name,
                       position, phone, salary.
        """
        return cls(
            id=row[0],
            last_name=row[1],
            first_name=row[2],
            middle_name=row[3],
            position=row[4],
            phone=row[5],
            salary=row[6],
        )
