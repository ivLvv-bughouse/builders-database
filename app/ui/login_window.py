"""Диалоговое окно входа в систему.

Показывается при старте приложения. Блокирует главное окно (grab_set)
до тех пор, пока пользователь не войдёт или не закроет окно.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import USERS


class LoginDialog(tk.Toplevel):
    """Модальное окно аутентификации.

    После закрытия проверяйте атрибут authenticated:
        dlg = LoginDialog(parent)
        parent.wait_window(dlg)
        if dlg.authenticated: ...
    """

    def __init__(self, parent: tk.Tk):
        super().__init__(parent)
        self.authenticated: bool = False
        self.role: str = ""
        self.user_display: str = ""

        self.title("Вход в систему")
        self.resizable(False, False)
        self.grab_set()                          # блокировать главное окно
        self.protocol("WM_DELETE_WINDOW", self._cancel)

        self._build()
        # Центрировать окно на экране
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    def _build(self):
        """Собирает форму входа."""
        pad = {"padx": 12, "pady": 5}

        # Заголовок
        ttk.Label(
            self, text="Строительная компания", font=("", 13, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(14, 2))
        ttk.Label(
            self, text="Вход в систему", foreground="gray"
        ).grid(row=1, column=0, columnspan=2, pady=(0, 10))

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=2, column=0, columnspan=2, sticky=tk.EW, padx=10
        )

        # Поле логина — выбор из Combobox со всеми доступными логинами
        ttk.Label(self, text="Логин:").grid(row=3, column=0, sticky=tk.E, **pad)
        self._login_var = tk.StringVar()
        login_cb = ttk.Combobox(
            self, textvariable=self._login_var,
            values=list(USERS.keys()), state="readonly", width=22
        )
        login_cb.grid(row=3, column=1, sticky=tk.W, **pad)
        login_cb.current(0)

        # Поле пароля
        ttk.Label(self, text="Пароль:").grid(row=4, column=0, sticky=tk.E, **pad)
        self._pass_var = tk.StringVar()
        pass_entry = ttk.Entry(self, textvariable=self._pass_var, show="*", width=24)
        pass_entry.grid(row=4, column=1, sticky=tk.W, **pad)
        pass_entry.bind("<Return>", lambda _: self._login())

        # Кнопка входа
        ttk.Button(self, text="Войти", command=self._login).grid(
            row=5, column=0, columnspan=2, pady=(6, 4)
        )

        ttk.Separator(self, orient=tk.HORIZONTAL).grid(
            row=6, column=0, columnspan=2, sticky=tk.EW, padx=10, pady=(4, 0)
        )

        # Справка по учётным записям
        hint_text = (
            "Учётные записи (пароль для всех: 1234)\n"
            "admin       — Администратор  (все разделы)\n"
            "director    — Руководитель   (все разделы)\n"
            "accountant  — Бухгалтер      (Договоры, Отчёты)\n"
            "lawyer      — Юрист          (Клиенты, Объекты, Договоры)\n"
            "sales       — Продажник      (Клиенты, Объекты, Договоры)"
        )
        ttk.Label(
            self, text=hint_text, foreground="gray", font=("", 8),
            justify=tk.LEFT
        ).grid(row=7, column=0, columnspan=2, sticky=tk.W, padx=14, pady=(4, 12))

    def _login(self):
        """Проверяет логин и пароль; при успехе устанавливает атрибуты и закрывает окно."""
        login = self._login_var.get().strip()
        password = self._pass_var.get()

        user = USERS.get(login)
        if user is None or user["password"] != password:
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.", parent=self)
            return

        self.authenticated = True
        self.role = user["role"]
        self.user_display = user["display"]
        self.destroy()

    def _cancel(self):
        """Закрывает диалог без аутентификации."""
        self.authenticated = False
        self.destroy()
