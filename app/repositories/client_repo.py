"""Репозиторий для работы с таблицей clients."""

from typing import Optional

from app.database import AppError, get_connection
from app.models.client import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository):
    """Реализует CRUD-операции для сущности «Клиент».

    Весь SQL сосредоточен здесь; UI-слой вызывает только методы этого класса.
    """

    def __init__(self):
        """Получает соединение из синглтона database.py."""
        self._conn = get_connection()

    def get_all(self) -> list[Client]:
        """Возвращает список всех клиентов, отсортированных по фамилии."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать всех клиентов, упорядочив по фамилии и имени
                cur.execute(
                    "SELECT id, last_name, first_name, middle_name, "
                    "phone, email, passport, client_type "
                    "FROM clients ORDER BY last_name, first_name"
                )
                return [Client.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_id(self, id: int) -> Optional[Client]:
        """Возвращает клиента по его id или None, если запись не найдена."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать одного клиента по первичному ключу
                cur.execute(
                    "SELECT id, last_name, first_name, middle_name, "
                    "phone, email, passport, client_type "
                    "FROM clients WHERE id = %s",
                    (id,),
                )
                row = cur.fetchone()
                return Client.from_row(row) if row else None
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def create(self, entity: Client) -> Client:
        """Вставляет нового клиента в БД и возвращает объект с присвоенным id."""
        try:
            with self._conn.cursor() as cur:
                # Вставить клиента и получить сгенерированный id через RETURNING
                cur.execute(
                    "INSERT INTO clients "
                    "(last_name, first_name, middle_name, phone, email, passport, client_type) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
                    (
                        entity.last_name,
                        entity.first_name,
                        entity.middle_name,
                        entity.phone,
                        entity.email,
                        entity.passport,
                        entity.client_type,
                    ),
                )
                entity.id = cur.fetchone()[0]
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update(self, entity: Client) -> Client:
        """Обновляет данные существующего клиента в БД."""
        try:
            with self._conn.cursor() as cur:
                # Обновить все поля клиента по его id
                cur.execute(
                    "UPDATE clients SET last_name=%s, first_name=%s, middle_name=%s, "
                    "phone=%s, email=%s, passport=%s, client_type=%s WHERE id=%s",
                    (
                        entity.last_name,
                        entity.first_name,
                        entity.middle_name,
                        entity.phone,
                        entity.email,
                        entity.passport,
                        entity.client_type,
                        entity.id,
                    ),
                )
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def delete(self, id: int) -> bool:
        """Удаляет клиента по id. Возвращает True, если строка была удалена."""
        try:
            with self._conn.cursor() as cur:
                # Удалить клиента с данным id
                cur.execute("DELETE FROM clients WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
                self._conn.commit()
                return deleted
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e
