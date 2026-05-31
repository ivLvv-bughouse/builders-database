"""Генератор отчётов строительной компании.

Каждая функция выполняет аналитический SQL-запрос с JOIN-ами и возвращает
список словарей — готовые данные для отображения в Treeview.
SQL-запросы не дублируются в UI; весь доступ к БД только здесь.
"""

from app.database import AppError, get_connection


def get_contract_summaries() -> list[dict]:
    """Возвращает краткий список всех договоров для автодополнения в UI.

    Каждый элемент содержит id, имя клиента и дату — для отображения
    в выпадающем списке отчёта по договору.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Получить id, ФИО клиента и дату каждого договора для списка выбора
            cur.execute(
                """
                SELECT con.id,
                       c.last_name || ' ' || c.first_name AS client,
                       con.contract_date,
                       con.amount
                FROM contracts con
                JOIN clients c ON con.client_id = c.id
                ORDER BY con.id
                """
            )
            return [
                {
                    "id": row[0],
                    "client": row[1],
                    "contract_date": row[2],
                    "amount": row[3],
                }
                for row in cur.fetchall()
            ]
    except Exception as e:
        conn.rollback()
        raise AppError(str(e)) from e


def get_date_range() -> tuple[str, str]:
    """Возвращает минимальную и максимальную даты договоров в базе.

    Используется кнопкой «Весь период» для автозаполнения дат в отчётах.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Найти крайние даты среди всех договоров
            cur.execute("SELECT MIN(contract_date), MAX(contract_date) FROM contracts")
            row = cur.fetchone()
            if row and row[0]:
                return str(row[0]), str(row[1])
            return "2024-01-01", "2025-12-31"
    except Exception as e:
        conn.rollback()
        raise AppError(str(e)) from e


def sales_contract_report(contract_id: int) -> list[dict]:
    """Формирует отчёт по договору купли-продажи.

    Возвращает полную информацию о договоре: данные клиента, объекта,
    здания, суммы и статуса сделки.

    Args:
        contract_id: Первичный ключ договора в таблице contracts.

    Returns:
        Список из одного словаря с данными договора (пустой, если не найден).
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Получить полную информацию о договоре с данными клиента,
            # объекта и здания через JOIN
            cur.execute(
                """
                SELECT c.last_name,
                       c.first_name,
                       c.middle_name,
                       p.property_type,
                       p.area,
                       p.price,
                       con.contract_date,
                       con.status,
                       con.amount,
                       b.address
                FROM contracts con
                JOIN clients    c ON con.client_id    = c.id
                JOIN properties p ON con.property_id  = p.id
                JOIN buildings  b ON p.building_id    = b.id
                WHERE con.id = %s
                """,
                (contract_id,),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(
                    {
                        "client_name": f"{row[0]} {row[1]}" + (f" {row[2]}" if row[2] else ""),
                        "property_type": row[3],
                        "area": row[4],
                        "price": row[5],
                        "contract_date": row[6],
                        "status": row[7],
                        "amount": row[8],
                        "address": row[9],
                    }
                )
            return result
    except Exception as e:
        raise AppError(str(e)) from e


def deals_by_employee_report(date_from: str, date_to: str) -> list[dict]:
    """Формирует реестр сделок по сотрудникам за указанный период.

    Показывает, какие договоры оформил каждый сотрудник, с какими клиентами
    и по каким объектам.

    Args:
        date_from: Начало периода в формате 'YYYY-MM-DD'.
        date_to:   Конец периода в формате 'YYYY-MM-DD'.

    Returns:
        Список словарей: сотрудник, клиент, тип объекта, сумма, дата.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Выбрать все сделки за период, сгруппировав по сотруднику (ORDER BY)
            cur.execute(
                """
                SELECT e.last_name,
                       e.first_name,
                       c.last_name  AS client_last,
                       c.first_name AS client_first,
                       p.property_type,
                       con.amount,
                       con.contract_date
                FROM contracts con
                JOIN employees  e ON con.employee_id = e.id
                JOIN clients    c ON con.client_id   = c.id
                JOIN properties p ON con.property_id = p.id
                WHERE con.contract_date BETWEEN %s AND %s
                ORDER BY e.last_name, e.first_name
                """,
                (date_from, date_to),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(
                    {
                        "employee": f"{row[0]} {row[1]}",
                        "client": f"{row[2]} {row[3]}",
                        "property_type": row[4],
                        "amount": row[5],
                        "contract_date": row[6],
                    }
                )
            return result
    except Exception as e:
        raise AppError(str(e)) from e


def revenue_by_property_type_report(date_from: str, date_to: str) -> list[dict]:
    """Формирует сводку выручки по типам объектов за указанный период.

    Агрегирует данные: количество сделок и общая сумма для каждого типа объекта.

    Args:
        date_from: Начало периода в формате 'YYYY-MM-DD'.
        date_to:   Конец периода в формате 'YYYY-MM-DD'.

    Returns:
        Список словарей: тип объекта, количество сделок, общая выручка.
        Отсортирован по убыванию выручки.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Агрегировать выручку по типу объекта, отсортировав по убыванию суммы
            cur.execute(
                """
                SELECT p.property_type,
                       COUNT(*)       AS deal_count,
                       SUM(con.amount) AS total_revenue
                FROM contracts con
                JOIN properties p ON con.property_id = p.id
                WHERE con.contract_date BETWEEN %s AND %s
                GROUP BY p.property_type
                ORDER BY total_revenue DESC
                """,
                (date_from, date_to),
            )
            rows = cur.fetchall()
            result = []
            for row in rows:
                result.append(
                    {
                        "property_type": row[0],
                        "deal_count": row[1],
                        "total_revenue": row[2],
                    }
                )
            return result
    except Exception as e:
        raise AppError(str(e)) from e
