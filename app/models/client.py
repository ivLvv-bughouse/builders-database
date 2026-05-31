"""Модель клиента строительной компании."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Client:
    """Клиент — физическое или юридическое лицо, покупающее объект недвижимости.

    Поля соответствуют столбцам таблицы clients в базе данных.
    id=None при создании нового клиента (до вставки в БД).
    """

    last_name: str
    first_name: str
    phone: str
    passport: str
    client_type: str
    middle_name: Optional[str] = None
    email: Optional[str] = None
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Client":
        """Создаёт объект Client из строки результата psycopg2-запроса.

        Порядок полей: id, last_name, first_name, middle_name,
                       phone, email, passport, client_type.
        """
        return cls(
            id=row[0],
            last_name=row[1],
            first_name=row[2],
            middle_name=row[3],
            phone=row[4],
            email=row[5],
            passport=row[6],
            client_type=row[7],
        )
