"""Репозиторий для работы с таблицей contracts."""

from typing import Optional

from app.database import AppError, get_connection
from app.models.contract import Contract
from app.repositories.base import BaseRepository


class ContractRepository(BaseRepository):
    """Реализует CRUD-операции для сущности «Договор».

    Дополнительные методы позволяют фильтровать договоры по сотруднику,
    клиенту и статусу — типичные операции для отчётности.
    """

    def __init__(self):
        """Получает соединение из синглтона database.py."""
        self._conn = get_connection()

    def get_all(self) -> list[Contract]:
        """Возвращает список всех договоров, отсортированных по дате (новые первыми)."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать все договоры, упорядочив по дате убывания
                cur.execute(
                    "SELECT id, contract_date, amount, status, "
                    "client_id, employee_id, property_id "
                    "FROM contracts ORDER BY contract_date DESC"
                )
                return [Contract.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_id(self, id: int) -> Optional[Contract]:
        """Возвращает договор по его id или None, если запись не найдена."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать один договор по первичному ключу
                cur.execute(
                    "SELECT id, contract_date, amount, status, "
                    "client_id, employee_id, property_id "
                    "FROM contracts WHERE id = %s",
                    (id,),
                )
                row = cur.fetchone()
                return Contract.from_row(row) if row else None
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def create(self, entity: Contract) -> Contract:
        """Вставляет новый договор в БД и возвращает объект с присвоенным id."""
        try:
            with self._conn.cursor() as cur:
                # Вставить договор и получить сгенерированный id через RETURNING
                cur.execute(
                    "INSERT INTO contracts "
                    "(contract_date, amount, status, client_id, employee_id, property_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (
                        entity.contract_date,
                        entity.amount,
                        entity.status,
                        entity.client_id,
                        entity.employee_id,
                        entity.property_id,
                    ),
                )
                entity.id = cur.fetchone()[0]
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update(self, entity: Contract) -> Contract:
        """Обновляет данные существующего договора в БД."""
        try:
            with self._conn.cursor() as cur:
                # Обновить все поля договора по его id
                cur.execute(
                    "UPDATE contracts SET contract_date=%s, amount=%s, status=%s, "
                    "client_id=%s, employee_id=%s, property_id=%s WHERE id=%s",
                    (
                        entity.contract_date,
                        entity.amount,
                        entity.status,
                        entity.client_id,
                        entity.employee_id,
                        entity.property_id,
                        entity.id,
                    ),
                )
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def delete(self, id: int) -> bool:
        """Удаляет договор по id. Возвращает True, если строка была удалена."""
        try:
            with self._conn.cursor() as cur:
                # Удалить договор с данным id
                cur.execute("DELETE FROM contracts WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
                self._conn.commit()
                return deleted
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_employee(self, employee_id: int) -> list[Contract]:
        """Возвращает все договоры, оформленные указанным сотрудником."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать договоры конкретного сотрудника
                cur.execute(
                    "SELECT id, contract_date, amount, status, "
                    "client_id, employee_id, property_id "
                    "FROM contracts WHERE employee_id = %s ORDER BY contract_date DESC",
                    (employee_id,),
                )
                return [Contract.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_client(self, client_id: int) -> list[Contract]:
        """Возвращает все договоры указанного клиента."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать договоры конкретного клиента
                cur.execute(
                    "SELECT id, contract_date, amount, status, "
                    "client_id, employee_id, property_id "
                    "FROM contracts WHERE client_id = %s ORDER BY contract_date DESC",
                    (client_id,),
                )
                return [Contract.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_status(self, status: str) -> list[Contract]:
        """Возвращает все договоры с указанным статусом (оформлен/завершён/расторгнут)."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать договоры, отфильтровав по статусу
                cur.execute(
                    "SELECT id, contract_date, amount, status, "
                    "client_id, employee_id, property_id "
                    "FROM contracts WHERE status = %s ORDER BY contract_date DESC",
                    (status,),
                )
                return [Contract.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e
