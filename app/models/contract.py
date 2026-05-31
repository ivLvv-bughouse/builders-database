"""Модель договора купли-продажи объекта недвижимости."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional


@dataclass
class Contract:
    """Договор купли-продажи между клиентом и компанией.

    Связывает клиента, сотрудника и объект недвижимости.
    Поля соответствуют столбцам таблицы contracts в базе данных.
    status ∈ {'оформлен', 'завершён', 'расторгнут'}
    """

    contract_date: date
    amount: Decimal
    status: str
    client_id: int
    employee_id: int
    property_id: int
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row: tuple) -> "Contract":
        """Создаёт объект Contract из строки результата psycopg2-запроса.

        Порядок полей: id, contract_date, amount, status,
                       client_id, employee_id, property_id.
        """
        return cls(
            id=row[0],
            contract_date=row[1],
            amount=row[2],
            status=row[3],
            client_id=row[4],
            employee_id=row[5],
            property_id=row[6],
        )
