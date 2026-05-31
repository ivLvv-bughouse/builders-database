"""Точка входа в приложение строительной компании.

Порядок запуска:
1. Загрузить переменные окружения из .env
2. Проверить соединение с базой данных
3. Показать диалог входа (внутри MainWindow.__init__)
4. Запустить главное окно tkinter
"""

import sys

from dotenv import load_dotenv

# Загрузить .env до импорта модулей приложения, чтобы os.getenv работал корректно
load_dotenv()

from app.database import AppError, test_connection  # noqa: E402
from app.ui.main_window import MainWindow           # noqa: E402


def main():
    """Главная функция: проверка БД, показ логина и запуск GUI."""
    try:
        test_connection()
    except AppError as e:
        print(f"Ошибка подключения к БД: {e}", file=sys.stderr)
        sys.exit(1)

    app = MainWindow()

    # Если пользователь закрыл окно логина без входа — выйти без ошибки
    if not app._authenticated:
        app.destroy()
        sys.exit(0)

    app.mainloop()


if __name__ == "__main__":
    main()
