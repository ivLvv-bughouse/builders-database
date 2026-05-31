"""Модуль подключения к базе данных PostgreSQL.

Реализует паттерн «Синглтон» для соединения: создаётся одно соединение
на весь жизненный цикл приложения и переиспользуется во всех репозиториях.
"""

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


class AppError(Exception):
    """Базовое исключение приложения.

    Все репозитории перехватывают низкоуровневые ошибки psycopg2
    и оборачивают их в AppError, чтобы UI-слой работал только с одним типом ошибок.
    """


_connection = None  # единственный экземпляр соединения (синглтон)


def get_connection():
    """Возвращает активное соединение с базой данных.

    При первом вызове создаёт соединение, используя параметры из .env.
    При повторных вызовах возвращает уже существующее соединение.
    """
    global _connection
    if _connection is None or _connection.closed:
        _connection = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", 5432)),
            dbname=os.getenv("DB_NAME", "construction_db"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", ""),
        )
        # autocommit=False — транзакции управляются вручную через commit/rollback
        _connection.autocommit = False
    return _connection


def close_connection():
    """Закрывает соединение с базой данных и обнуляет синглтон."""
    global _connection
    if _connection is not None and not _connection.closed:
        _connection.close()
    _connection = None


def test_connection():
    """Проверяет работоспособность соединения с БД.

    Вызывается при старте приложения. Выбрасывает AppError, если
    подключение не удалось, чтобы main.py мог завершить работу с сообщением.
    """
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        print("DB connected successfully")
    except Exception as e:
        raise AppError(f"Не удалось подключиться к базе данных: {e}") from e
