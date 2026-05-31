"""Репозиторий для работы с таблицей properties."""

from typing import Optional

from app.database import AppError, get_connection
from app.models.property import Property
from app.repositories.base import BaseRepository


class PropertyRepository(BaseRepository):
    """Реализует CRUD-операции для сущности «Объект недвижимости».

    Дополнительные методы позволяют фильтровать объекты по статусу,
    типу и зданию — это часто нужно при оформлении договоров.
    """

    def __init__(self):
        """Получает соединение из синглтона database.py."""
        self._conn = get_connection()

    def get_all(self) -> list[Property]:
        """Возвращает список всех объектов, отсортированных по типу и номеру."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать все объекты недвижимости, упорядочив по типу и номеру
                cur.execute(
                    "SELECT id, property_type, number, area, price, status, building_id "
                    "FROM properties ORDER BY property_type, number"
                )
                return [Property.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_id(self, id: int) -> Optional[Property]:
        """Возвращает объект недвижимости по его id или None."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать один объект по первичному ключу
                cur.execute(
                    "SELECT id, property_type, number, area, price, status, building_id "
                    "FROM properties WHERE id = %s",
                    (id,),
                )
                row = cur.fetchone()
                return Property.from_row(row) if row else None
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def create(self, entity: Property) -> Property:
        """Вставляет новый объект в БД и возвращает его с присвоенным id."""
        try:
            with self._conn.cursor() as cur:
                # Вставить объект и получить сгенерированный id через RETURNING
                cur.execute(
                    "INSERT INTO properties "
                    "(property_type, number, area, price, status, building_id) "
                    "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (
                        entity.property_type,
                        entity.number,
                        entity.area,
                        entity.price,
                        entity.status,
                        entity.building_id,
                    ),
                )
                entity.id = cur.fetchone()[0]
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update(self, entity: Property) -> Property:
        """Обновляет данные существующего объекта в БД."""
        try:
            with self._conn.cursor() as cur:
                # Обновить все поля объекта по его id
                cur.execute(
                    "UPDATE properties SET property_type=%s, number=%s, area=%s, "
                    "price=%s, status=%s, building_id=%s WHERE id=%s",
                    (
                        entity.property_type,
                        entity.number,
                        entity.area,
                        entity.price,
                        entity.status,
                        entity.building_id,
                        entity.id,
                    ),
                )
                self._conn.commit()
                return entity
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def delete(self, id: int) -> bool:
        """Удаляет объект по id. Возвращает True, если строка была удалена."""
        try:
            with self._conn.cursor() as cur:
                # Удалить объект с данным id
                cur.execute("DELETE FROM properties WHERE id = %s", (id,))
                deleted = cur.rowcount > 0
                self._conn.commit()
                return deleted
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_by_status(self, status: str) -> list[Property]:
        """Возвращает объекты с указанным статусом (свободен/забронирован/продан)."""
        try:
            with self._conn.cursor() as cur:
                # Выбрать объекты, отфильтровав по статусу
                cur.execute(
                    "SELECT id, property_type, number, area, price, status, building_id "
                    "FROM properties WHERE status = %s ORDER BY property_type, number",
                    (status,),
                )
                return [Property.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def get_free_by_type_and_building(
        self, property_type: str, building_id: int
    ) -> list[Property]:
        """Возвращает свободные объекты заданного типа в конкретном здании.

        Используется при выборе объекта для нового договора.
        """
        try:
            with self._conn.cursor() as cur:
                # Выбрать свободные объекты нужного типа в указанном здании
                cur.execute(
                    "SELECT id, property_type, number, area, price, status, building_id "
                    "FROM properties "
                    "WHERE status = 'свободен' AND property_type = %s AND building_id = %s "
                    "ORDER BY number",
                    (property_type, building_id),
                )
                return [Property.from_row(row) for row in cur.fetchall()]
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e

    def update_status(self, property_id: int, new_status: str) -> bool:
        """Изменяет статус объекта недвижимости (например, при заключении договора)."""
        try:
            with self._conn.cursor() as cur:
                # Обновить только поле status у конкретного объекта
                cur.execute(
                    "UPDATE properties SET status = %s WHERE id = %s",
                    (new_status, property_id),
                )
                updated = cur.rowcount > 0
                self._conn.commit()
                return updated
        except Exception as e:
            self._conn.rollback()
            raise AppError(str(e)) from e
