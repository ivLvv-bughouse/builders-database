"""Репозиторий для работы с таблицей buildings."""

from typing import Optional

from app.database import AppError, get_connection
from app.models.building import Building
from app.repositories.base import BaseRepository


class BuildingRepository(BaseRepository):
    """Реализует CRUD-операции для сущности «Здание»."""

    def __init__(self):
        """Получает соединение из синглтона database.py."""
        self._conn = get_connection()

    def get_all(self) -> list[Building]:
        """Возвращает список всех зданий, отсортированных по названию."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать все здания, упорядочив по названию
                cur.execute(
                    "SELECT id, name, address, floors, completion_date "
                    "FROM buildings ORDER BY name"
                )
                return [Building.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_id(self, id: int) -> Optional[Building]:
        """Возвращает здание по его id или None, если запись не найдена."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать одно здание по первичному ключу
                cur.execute(
                    "SELECT id, name, address, floors, completion_date "
                    "FROM buildings WHERE id = %s",
                    (id,),
                )
                row = cur.fetchone()
                return Building.from_row(row) if row else None
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def create(self, entity: Building) -> Building:
        """Вставляет новое здание в БД и возвращает объект с присвоенным id."""
        try:
            with self._conn.cursor() as cur:
                # Вставить здание и получить сгенерированный id через RETURNING
                cur.execute(
                    "INSERT INTO buildings (name, address, floors, completion_date) "
                    "VALUES (%s, %s, %s, %s) RETURNING id",
                    (
                        entity.name,
                        entity.address,
                        entity.floors,
                        entity.completion_date,
                    ),
                )
                entity.id = cur.fetchone()[0]
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update(self, entity: Building) -> Building:
        """Обновляет данные существующего здания в БД."""
        try:
            with self._conn.cursor() as cur:
                # Обновить все поля здания по его id
                cur.execute(
                    "UPDATE buildings SET name=%s, address=%s, floors=%s, "
                    "completion_date=%s WHERE id=%s",
                    (
                        entity.name,
                        entity.address,
                        entity.floors,
                        entity.completion_date,
                        entity.id,
                    ),
                )
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def delete(self, id: int) -> bool:
        """Удаляет здание по id. Возвращает True, если строка была удалена."""
        try:
            with self._conn.cursor() as cur:
                # Удалить здание с данным id
                cur.execute("DELETE FROM buildings WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
                self._conn.commit()
                return deleted
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e
