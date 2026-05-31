"""Репозиторий для работы с таблицей employees."""

from typing import Optional

from app.database import AppError, get_connection
from app.models.employee import Employee
from app.repositories.base import BaseRepository


class EmployeeRepository(BaseRepository):
    """Реализует CRUD-операции для сущности «Сотрудник»."""

    def __init__(self):
        """Получает соединение из синглтона database.py."""
        self._conn = get_connection()

    def get_all(self) -> list[Employee]:
        """Возвращает список всех сотрудников, отсортированных по фамилии."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать всех сотрудников, упорядочив по фамилии
                cur.execute(
                    "SELECT id, last_name, first_name, middle_name, position, phone, salary "
                    "FROM employees ORDER BY last_name, first_name"
                )
                return [Employee.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_id(self, id: int) -> Optional[Employee]:
        """Возвращает сотрудника по его id или None, если запись не найдена."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать одного сотрудника по первичному ключу
                cur.execute(
                    "SELECT id, last_name, first_name, middle_name, position, phone, salary "
                    "FROM employees WHERE id = %s",
                    (id,),
                )
                row = cur.fetchone()
                return Employee.from_row(row) if row else None
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def create(self, entity: Employee) -> Employee:
        """Вставляет нового сотрудника в БД и возвращает объект с присвоенным id."""
        try:
            with self._conn.cursor() as cur:
                # Вставить сотрудника и получить сгенерированный id через RETURNING
                cur.execute(
                    "INSERT INTO employees "
                    "(last_name, first_name, middle_name, position, phone, salary) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (
                        entity.last_name,
                        entity.first_name,
                        entity.middle_name,
                        entity.position,
                        entity.phone,
                        entity.salary,
                    ),
                )
                entity.id = cur.fetchone()[0]
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update(self, entity: Employee) -> Employee:
        """Обновляет данные существующего сотрудника в БД."""
        try:
            with self._conn.cursor() as cur:
                # Обновить все поля сотрудника по его id
                cur.execute(
                    "UPDATE employees SET last_name=%s, first_name=%s, middle_name=%s, "
                    "position=%s, phone=%s, salary=%s WHERE id=%s",
                    (
                        entity.last_name,
                        entity.first_name,
                        entity.middle_name,
                        entity.position,
                        entity.phone,
                        entity.salary,
                        entity.id,
                    ),
                )
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def delete(self, id: int) -> bool:
        """Удаляет сотрудника по id. Возвращает True, если строка была удалена."""
        try:
            with self._conn.cursor() as cur:
                # Удалить сотрудника с данным id
                cur.execute("DELETE FROM employees WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
                self._conn.commit()
                return deleted
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e
