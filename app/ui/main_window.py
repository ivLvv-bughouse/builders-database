"""Главное окно приложения строительной компании.

Реализует интерфейс на tkinter/ttk с шестью вкладками (Notebook):
клиенты, сотрудники, здания, объекты, договоры, отчёты.
Набор доступных вкладок определяется ролью вошедшего пользователя.
UI не содержит SQL — весь доступ к данным через репозитории и report_generator.
"""

import tkinter as tk
from tkinter import messagebox, ttk

from app.auth import ROLE_TABS
from app.models.building import Building
from app.models.client import Client
from app.models.contract import Contract
from app.models.employee import Employee
from app.models.property import Property
from app.repositories.building_repo import BuildingRepository
from app.repositories.client_repo import ClientRepository
from app.repositories.contract_repo import ContractRepository
from app.repositories.employee_repo import EmployeeRepository
from app.repositories.property_repo import PropertyRepository
from app.ui.login_window import LoginDialog
from reports.report_generator import (
    deals_by_employee_report,
    get_contract_summaries,
    get_date_range,
    revenue_by_property_type_report,
    sales_contract_report,
)


# ---------------------------------------------------------------------------
# Вспомогательные утилиты
# ---------------------------------------------------------------------------

def _clear_tree(tree: ttk.Treeview):
    """Удаляет все строки из Treeview перед обновлением данных."""
    for row in tree.get_children():
        tree.delete(row)


class _AutoCombo(ttk.Combobox):
    """Combobox с фильтрацией по набираемому тексту.

    При наборе символов список значений сужается до строк,
    содержащих введённый фрагмент (регистронезависимо).
    """

    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._all_options: list[str] = []
        self.bind("<KeyRelease>", self._on_key)

    def load(self, options: list[str]):
        """Загружает полный список опций и сохраняет его как эталон."""
        self._all_options = options
        self["values"] = options

    def _on_key(self, event):
        """Фильтрует список при каждом нажатии клавиши."""
        if event.keysym in ("Return", "Tab", "Escape", "Down", "Up"):
            return
        typed = self.get().lower()
        filtered = (
            [o for o in self._all_options if typed in o.lower()]
            if typed else self._all_options
        )
        self["values"] = filtered


# ---------------------------------------------------------------------------
# Главное окно
# ---------------------------------------------------------------------------

class MainWindow(tk.Tk):
    """Главное окно приложения.

    При инициализации сначала показывает диалог входа;
    если пользователь отменил — окно уничтожается без отображения.
    Набор вкладок формируется на основе роли пользователя из ROLE_TABS.
    """

    def __init__(self):
        super().__init__()
        self._authenticated = False
        self.withdraw()  # скрыть пустое окно до успешного входа

        dlg = LoginDialog(self)
        self.wait_window(dlg)

        if not dlg.authenticated:
            return  # main.py проверит _authenticated и завершит процесс

        self._authenticated = True
        self._role = dlg.role
        self._user_display = dlg.user_display

        self.deiconify()
        self._build_ui()

    def _build_ui(self):
        """Строит интерфейс после успешной аутентификации."""
        self.title(
            f"Строительная компания — БД  |  {self._user_display}  [{self._role}]"
        )
        self.geometry("1100x660")
        self.minsize(900, 560)

        # Инициализация репозиториев (одно соединение — синглтон)
        self._clients    = ClientRepository()
        self._employees  = EmployeeRepository()
        self._buildings  = BuildingRepository()
        self._properties = PropertyRepository()
        self._contracts  = ContractRepository()

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Фабрика вкладок — создаётся только то, что разрешено роли
        builders = {
            "Клиенты":    lambda: ClientsTab(notebook, self._clients),
            "Сотрудники": lambda: EmployeesTab(notebook, self._employees),
            "Здания":     lambda: BuildingsTab(notebook, self._buildings),
            "Объекты":    lambda: PropertiesTab(notebook, self._properties, self._buildings),
            "Договоры":   lambda: ContractsTab(
                notebook, self._contracts,
                self._clients, self._employees, self._properties
            ),
            "Отчёты":     lambda: ReportsTab(notebook),
        }

        for tab_name in [
            "Клиенты", "Сотрудники", "Здания",
            "Объекты", "Договоры", "Отчёты"
        ]:
            if tab_name in ROLE_TABS[self._role]:
                tab = builders[tab_name]()
                notebook.add(tab, text=f"  {tab_name}  ")


# ---------------------------------------------------------------------------
# Вкладка «Клиенты»
# ---------------------------------------------------------------------------

class ClientsTab(ttk.Frame):
    """Вкладка для просмотра и редактирования таблицы клиентов."""

    COLUMNS = ("id", "last_name", "first_name", "middle_name",
               "phone", "email", "passport", "client_type")
    HEADERS = ("ID", "Фамилия", "Имя", "Отчество",
               "Телефон", "Email", "Паспорт", "Тип клиента")

    def __init__(self, parent, repo: ClientRepository):
        super().__init__(parent)
        self._repo = repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(
            frame_tree, columns=self.COLUMNS, show="headings", selectmode="browse"
        )
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=header)
            self._tree.column(col, width=100, anchor=tk.W)
        self._tree.column("id", width=40)

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        frame_btn = ttk.Frame(self)
        frame_btn.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(frame_btn, text="Добавить",      command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_btn, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_btn, text="Удалить",       command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(frame_btn, text="Обновить",      command=self.refresh).pack(side=tk.LEFT, padx=2)

    def refresh(self):
        try:
            _clear_tree(self._tree)
            for c in self._repo.get_all():
                self._tree.insert("", tk.END, values=(
                    c.id, c.last_name, c.first_name,
                    c.middle_name or "", c.phone,
                    c.email or "", c.passport, c.client_type,
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить клиентов:\n{e}")

    def _selected_id(self):
        sel = self._tree.selection()
        return int(self._tree.item(sel[0], "values")[0]) if sel else None

    def _add(self):
        ClientDialog(self, self._repo, mode="add", on_save=self.refresh)

    def _edit(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showwarning("Выбор", "Выберите клиента для редактирования.")
            return
        try:
            client = self._repo.get_by_id(cid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        ClientDialog(self, self._repo, mode="edit", entity=client, on_save=self.refresh)

    def _delete(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showwarning("Выбор", "Выберите клиента для удаления.")
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранного клиента?"):
            return
        try:
            self._repo.delete(cid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить клиента:\n{e}")


class ClientDialog(tk.Toplevel):
    """Модальный диалог добавления / редактирования клиента."""

    def __init__(self, parent, repo: ClientRepository, mode: str,
                 entity: Client = None, on_save=None):
        super().__init__(parent)
        self._repo, self._mode, self._entity, self._on_save = repo, mode, entity, on_save
        self.title("Добавить клиента" if mode == "add" else "Редактировать клиента")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if entity:
            self._fill(entity)

    def _build(self):
        fields = [
            ("Фамилия *",  "last_name"),  ("Имя *",      "first_name"),
            ("Отчество",   "middle_name"), ("Телефон *",  "phone"),
            ("Email",      "email"),       ("Паспорт *",  "passport"),
        ]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky=tk.W, padx=8, pady=3)
            var = tk.StringVar()
            ttk.Entry(self, textvariable=var, width=32).grid(row=i, column=1, padx=8, pady=3)
            self._vars[key] = var

        ttk.Label(self, text="Тип клиента *").grid(row=6, column=0, sticky=tk.W, padx=8, pady=3)
        self._type_var = tk.StringVar(value="физ. лицо")
        ttk.Combobox(self, textvariable=self._type_var,
                     values=["физ. лицо", "юр. лицо"],
                     state="readonly", width=30).grid(row=6, column=1, padx=8, pady=3)

        fb = ttk.Frame(self)
        fb.grid(row=7, column=0, columnspan=2, pady=8)
        ttk.Button(fb, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(fb, text="Отмена",    command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _fill(self, c: Client):
        self._vars["last_name"].set(c.last_name)
        self._vars["first_name"].set(c.first_name)
        self._vars["middle_name"].set(c.middle_name or "")
        self._vars["phone"].set(c.phone)
        self._vars["email"].set(c.email or "")
        self._vars["passport"].set(c.passport)
        self._type_var.set(c.client_type)

    def _save(self):
        ln = self._vars["last_name"].get().strip()
        fn = self._vars["first_name"].get().strip()
        ph = self._vars["phone"].get().strip()
        ps = self._vars["passport"].get().strip()
        if not (ln and fn and ph and ps):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (*).")
            return
        try:
            if self._mode == "add":
                self._repo.create(Client(
                    last_name=ln, first_name=fn,
                    middle_name=self._vars["middle_name"].get().strip() or None,
                    phone=ph,
                    email=self._vars["email"].get().strip() or None,
                    passport=ps, client_type=self._type_var.get(),
                ))
            else:
                self._entity.last_name   = ln
                self._entity.first_name  = fn
                self._entity.middle_name = self._vars["middle_name"].get().strip() or None
                self._entity.phone       = ph
                self._entity.email       = self._vars["email"].get().strip() or None
                self._entity.passport    = ps
                self._entity.client_type = self._type_var.get()
                self._repo.update(self._entity)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить клиента:\n{e}")


# ---------------------------------------------------------------------------
# Вкладка «Сотрудники»
# ---------------------------------------------------------------------------

class EmployeesTab(ttk.Frame):
    """Вкладка для просмотра и редактирования таблицы сотрудников."""

    COLUMNS = ("id", "last_name", "first_name", "middle_name", "position", "phone", "salary")
    HEADERS = ("ID", "Фамилия", "Имя", "Отчество", "Должность", "Телефон", "Зарплата")

    def __init__(self, parent, repo: EmployeeRepository):
        super().__init__(parent)
        self._repo = repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(frame_tree, columns=self.COLUMNS,
                                   show="headings", selectmode="browse")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=header)
            self._tree.column(col, width=110, anchor=tk.W)
        self._tree.column("id", width=40)
        self._tree.column("salary", width=90, anchor=tk.E)

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        fb = ttk.Frame(self)
        fb.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(fb, text="Добавить",      command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Удалить",       command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Обновить",      command=self.refresh).pack(side=tk.LEFT, padx=2)

    def refresh(self):
        try:
            _clear_tree(self._tree)
            for e in self._repo.get_all():
                self._tree.insert("", tk.END, values=(
                    e.id, e.last_name, e.first_name,
                    e.middle_name or "", e.position, e.phone, e.salary,
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить сотрудников:\n{e}")

    def _selected_id(self):
        sel = self._tree.selection()
        return int(self._tree.item(sel[0], "values")[0]) if sel else None

    def _add(self):
        EmployeeDialog(self, self._repo, mode="add", on_save=self.refresh)

    def _edit(self):
        eid = self._selected_id()
        if eid is None:
            messagebox.showwarning("Выбор", "Выберите сотрудника для редактирования.")
            return
        try:
            emp = self._repo.get_by_id(eid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        EmployeeDialog(self, self._repo, mode="edit", entity=emp, on_save=self.refresh)

    def _delete(self):
        eid = self._selected_id()
        if eid is None:
            messagebox.showwarning("Выбор", "Выберите сотрудника для удаления.")
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранного сотрудника?"):
            return
        try:
            self._repo.delete(eid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить сотрудника:\n{e}")


class EmployeeDialog(tk.Toplevel):
    """Модальный диалог добавления / редактирования сотрудника."""

    def __init__(self, parent, repo: EmployeeRepository, mode: str,
                 entity: Employee = None, on_save=None):
        super().__init__(parent)
        self._repo, self._mode, self._entity, self._on_save = repo, mode, entity, on_save
        self.title("Добавить сотрудника" if mode == "add" else "Редактировать сотрудника")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if entity:
            self._fill(entity)

    def _build(self):
        fields = [
            ("Фамилия *",  "last_name"),  ("Имя *",       "first_name"),
            ("Отчество",   "middle_name"), ("Должность *", "position"),
            ("Телефон *",  "phone"),       ("Зарплата *",  "salary"),
        ]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky=tk.W, padx=8, pady=3)
            var = tk.StringVar()
            ttk.Entry(self, textvariable=var, width=32).grid(row=i, column=1, padx=8, pady=3)
            self._vars[key] = var

        fb = ttk.Frame(self)
        fb.grid(row=6, column=0, columnspan=2, pady=8)
        ttk.Button(fb, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(fb, text="Отмена",    command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _fill(self, e: Employee):
        self._vars["last_name"].set(e.last_name)
        self._vars["first_name"].set(e.first_name)
        self._vars["middle_name"].set(e.middle_name or "")
        self._vars["position"].set(e.position)
        self._vars["phone"].set(e.phone)
        self._vars["salary"].set(str(e.salary))

    def _save(self):
        ln = self._vars["last_name"].get().strip()
        fn = self._vars["first_name"].get().strip()
        pos = self._vars["position"].get().strip()
        ph  = self._vars["phone"].get().strip()
        sal_str = self._vars["salary"].get().strip()
        if not (ln and fn and pos and ph and sal_str):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (*).")
            return
        try:
            salary = float(sal_str)
            if salary <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Зарплата должна быть положительным числом.")
            return
        try:
            if self._mode == "add":
                self._repo.create(Employee(
                    last_name=ln, first_name=fn,
                    middle_name=self._vars["middle_name"].get().strip() or None,
                    position=pos, phone=ph, salary=salary,
                ))
            else:
                self._entity.last_name   = ln
                self._entity.first_name  = fn
                self._entity.middle_name = self._vars["middle_name"].get().strip() or None
                self._entity.position    = pos
                self._entity.phone       = ph
                self._entity.salary      = salary
                self._repo.update(self._entity)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить сотрудника:\n{e}")


# ---------------------------------------------------------------------------
# Вкладка «Здания»
# ---------------------------------------------------------------------------

class BuildingsTab(ttk.Frame):
    """Вкладка для просмотра и редактирования таблицы зданий."""

    COLUMNS = ("id", "name", "address", "floors", "completion_date")
    HEADERS = ("ID", "Название", "Адрес", "Этажей", "Дата сдачи")

    def __init__(self, parent, repo: BuildingRepository):
        super().__init__(parent)
        self._repo = repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(frame_tree, columns=self.COLUMNS,
                                   show="headings", selectmode="browse")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=header)
            self._tree.column(col, width=140, anchor=tk.W)
        self._tree.column("id", width=40)
        self._tree.column("floors", width=60, anchor=tk.CENTER)

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        fb = ttk.Frame(self)
        fb.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(fb, text="Добавить",      command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Удалить",       command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Обновить",      command=self.refresh).pack(side=tk.LEFT, padx=2)

    def refresh(self):
        try:
            _clear_tree(self._tree)
            for b in self._repo.get_all():
                self._tree.insert("", tk.END, values=(
                    b.id, b.name, b.address, b.floors, b.completion_date,
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить здания:\n{e}")

    def _selected_id(self):
        sel = self._tree.selection()
        return int(self._tree.item(sel[0], "values")[0]) if sel else None

    def _add(self):
        BuildingDialog(self, self._repo, mode="add", on_save=self.refresh)

    def _edit(self):
        bid = self._selected_id()
        if bid is None:
            messagebox.showwarning("Выбор", "Выберите здание для редактирования.")
            return
        try:
            building = self._repo.get_by_id(bid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        BuildingDialog(self, self._repo, mode="edit", entity=building, on_save=self.refresh)

    def _delete(self):
        bid = self._selected_id()
        if bid is None:
            messagebox.showwarning("Выбор", "Выберите здание для удаления.")
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранное здание?"):
            return
        try:
            self._repo.delete(bid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить здание:\n{e}")


class BuildingDialog(tk.Toplevel):
    """Модальный диалог добавления / редактирования здания."""

    def __init__(self, parent, repo: BuildingRepository, mode: str,
                 entity: Building = None, on_save=None):
        super().__init__(parent)
        self._repo, self._mode, self._entity, self._on_save = repo, mode, entity, on_save
        self.title("Добавить здание" if mode == "add" else "Редактировать здание")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if entity:
            self._fill(entity)

    def _build(self):
        fields = [
            ("Название *",    "name"),    ("Адрес *",                     "address"),
            ("Этажей *",      "floors"),  ("Дата сдачи * (ГГГГ-ММ-ДД)",  "completion_date"),
        ]
        self._vars = {}
        for i, (label, key) in enumerate(fields):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky=tk.W, padx=8, pady=3)
            var = tk.StringVar()
            ttk.Entry(self, textvariable=var, width=36).grid(row=i, column=1, padx=8, pady=3)
            self._vars[key] = var

        fb = ttk.Frame(self)
        fb.grid(row=4, column=0, columnspan=2, pady=8)
        ttk.Button(fb, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(fb, text="Отмена",    command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _fill(self, b: Building):
        self._vars["name"].set(b.name)
        self._vars["address"].set(b.address)
        self._vars["floors"].set(str(b.floors))
        self._vars["completion_date"].set(str(b.completion_date))

    def _save(self):
        name    = self._vars["name"].get().strip()
        address = self._vars["address"].get().strip()
        fl_str  = self._vars["floors"].get().strip()
        dt_str  = self._vars["completion_date"].get().strip()
        if not (name and address and fl_str and dt_str):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (*).")
            return
        try:
            floors = int(fl_str)
            if floors <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество этажей — положительное целое число.")
            return
        try:
            if self._mode == "add":
                self._repo.create(Building(name=name, address=address,
                                           floors=floors, completion_date=dt_str))
            else:
                self._entity.name            = name
                self._entity.address         = address
                self._entity.floors          = floors
                self._entity.completion_date = dt_str
                self._repo.update(self._entity)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить здание:\n{e}")


# ---------------------------------------------------------------------------
# Вкладка «Объекты»
# ---------------------------------------------------------------------------

class PropertiesTab(ttk.Frame):
    """Вкладка для просмотра и редактирования таблицы объектов недвижимости."""

    COLUMNS = ("id", "property_type", "number", "area", "price", "status", "building_id")
    HEADERS = ("ID", "Тип", "Номер", "Площадь, м²", "Цена, руб.", "Статус", "Здание (ID)")

    def __init__(self, parent, repo: PropertyRepository, building_repo: BuildingRepository):
        super().__init__(parent)
        self._repo = repo
        self._building_repo = building_repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(frame_tree, columns=self.COLUMNS,
                                   show="headings", selectmode="browse")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=header)
            self._tree.column(col, width=110, anchor=tk.W)
        self._tree.column("id", width=40)

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        fb = ttk.Frame(self)
        fb.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(fb, text="Добавить",      command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Удалить",       command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Обновить",      command=self.refresh).pack(side=tk.LEFT, padx=2)

    def refresh(self):
        try:
            _clear_tree(self._tree)
            for p in self._repo.get_all():
                self._tree.insert("", tk.END, values=(
                    p.id, p.property_type, p.number,
                    p.area, p.price, p.status, p.building_id,
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить объекты:\n{e}")

    def _selected_id(self):
        sel = self._tree.selection()
        return int(self._tree.item(sel[0], "values")[0]) if sel else None

    def _add(self):
        PropertyDialog(self, self._repo, self._building_repo, mode="add", on_save=self.refresh)

    def _edit(self):
        pid = self._selected_id()
        if pid is None:
            messagebox.showwarning("Выбор", "Выберите объект для редактирования.")
            return
        try:
            prop = self._repo.get_by_id(pid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        PropertyDialog(self, self._repo, self._building_repo,
                       mode="edit", entity=prop, on_save=self.refresh)

    def _delete(self):
        pid = self._selected_id()
        if pid is None:
            messagebox.showwarning("Выбор", "Выберите объект для удаления.")
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранный объект?"):
            return
        try:
            self._repo.delete(pid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить объект:\n{e}")


class PropertyDialog(tk.Toplevel):
    """Модальный диалог добавления / редактирования объекта недвижимости."""

    def __init__(self, parent, repo: PropertyRepository, building_repo: BuildingRepository,
                 mode: str, entity: Property = None, on_save=None):
        super().__init__(parent)
        self._repo, self._building_repo = repo, building_repo
        self._mode, self._entity, self._on_save = mode, entity, on_save
        self.title("Добавить объект" if mode == "add" else "Редактировать объект")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if entity:
            self._fill(entity)

    def _build(self):
        try:
            buildings = self._building_repo.get_all()
        except Exception:
            buildings = []
        self._building_map = {f"{b.name} (ID {b.id})": b.id for b in buildings}

        ttk.Label(self, text="Тип объекта *").grid(row=0, column=0, sticky=tk.W, padx=8, pady=3)
        self._type_var = tk.StringVar(value="квартира")
        ttk.Combobox(self, textvariable=self._type_var,
                     values=["квартира", "паркоместо", "коммерческое"],
                     state="readonly", width=30).grid(row=0, column=1, padx=8, pady=3)

        fields = [("Номер *", "number"), ("Площадь * (м²)", "area"), ("Цена * (руб.)", "price")]
        self._vars = {}
        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(self, text=label).grid(row=i, column=0, sticky=tk.W, padx=8, pady=3)
            var = tk.StringVar()
            ttk.Entry(self, textvariable=var, width=32).grid(row=i, column=1, padx=8, pady=3)
            self._vars[key] = var

        ttk.Label(self, text="Статус *").grid(row=4, column=0, sticky=tk.W, padx=8, pady=3)
        self._status_var = tk.StringVar(value="свободен")
        ttk.Combobox(self, textvariable=self._status_var,
                     values=["свободен", "забронирован", "продан"],
                     state="readonly", width=30).grid(row=4, column=1, padx=8, pady=3)

        ttk.Label(self, text="Здание *").grid(row=5, column=0, sticky=tk.W, padx=8, pady=3)
        self._building_var = tk.StringVar()
        labels = list(self._building_map.keys())
        ttk.Combobox(self, textvariable=self._building_var,
                     values=labels, state="readonly", width=30).grid(row=5, column=1, padx=8, pady=3)
        if labels:
            self._building_var.set(labels[0])

        fb = ttk.Frame(self)
        fb.grid(row=6, column=0, columnspan=2, pady=8)
        ttk.Button(fb, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(fb, text="Отмена",    command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _fill(self, p: Property):
        self._type_var.set(p.property_type)
        self._vars["number"].set(p.number)
        self._vars["area"].set(str(p.area))
        self._vars["price"].set(str(p.price))
        self._status_var.set(p.status)
        for label, bid in self._building_map.items():
            if bid == p.building_id:
                self._building_var.set(label)
                break

    def _save(self):
        number = self._vars["number"].get().strip()
        area_s = self._vars["area"].get().strip()
        price_s = self._vars["price"].get().strip()
        blabel = self._building_var.get()
        if not (number and area_s and price_s and blabel):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (*).")
            return
        try:
            area  = float(area_s)
            price = float(price_s)
            if area <= 0 or price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Площадь и цена должны быть положительными числами.")
            return
        bid = self._building_map.get(blabel)
        try:
            if self._mode == "add":
                self._repo.create(Property(
                    property_type=self._type_var.get(), number=number,
                    area=area, price=price,
                    status=self._status_var.get(), building_id=bid,
                ))
            else:
                self._entity.property_type = self._type_var.get()
                self._entity.number        = number
                self._entity.area          = area
                self._entity.price         = price
                self._entity.status        = self._status_var.get()
                self._entity.building_id   = bid
                self._repo.update(self._entity)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить объект:\n{e}")


# ---------------------------------------------------------------------------
# Вкладка «Договоры»
# ---------------------------------------------------------------------------

class ContractsTab(ttk.Frame):
    """Вкладка для просмотра и редактирования таблицы договоров."""

    COLUMNS = ("id", "contract_date", "amount", "status",
               "client_id", "employee_id", "property_id")
    HEADERS = ("ID", "Дата", "Сумма, руб.", "Статус",
               "Клиент (ID)", "Сотрудник (ID)", "Объект (ID)")

    def __init__(self, parent, repo: ContractRepository,
                 client_repo: ClientRepository,
                 employee_repo: EmployeeRepository,
                 property_repo: PropertyRepository):
        super().__init__(parent)
        self._repo = repo
        self._client_repo    = client_repo
        self._employee_repo  = employee_repo
        self._property_repo  = property_repo
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        frame_tree = ttk.Frame(self)
        frame_tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self._tree = ttk.Treeview(frame_tree, columns=self.COLUMNS,
                                   show="headings", selectmode="browse")
        for col, header in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=header)
            self._tree.column(col, width=110, anchor=tk.W)
        self._tree.column("id", width=40)
        self._tree.column("amount", anchor=tk.E)

        sb = ttk.Scrollbar(frame_tree, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        fb = ttk.Frame(self)
        fb.pack(fill=tk.X, padx=4, pady=4)
        ttk.Button(fb, text="Добавить",      command=self._add).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Редактировать", command=self._edit).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Удалить",       command=self._delete).pack(side=tk.LEFT, padx=2)
        ttk.Button(fb, text="Обновить",      command=self.refresh).pack(side=tk.LEFT, padx=2)

    def refresh(self):
        try:
            _clear_tree(self._tree)
            for c in self._repo.get_all():
                self._tree.insert("", tk.END, values=(
                    c.id, c.contract_date, c.amount, c.status,
                    c.client_id, c.employee_id, c.property_id,
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить договоры:\n{e}")

    def _selected_id(self):
        sel = self._tree.selection()
        return int(self._tree.item(sel[0], "values")[0]) if sel else None

    def _add(self):
        ContractDialog(self, self._repo, self._client_repo,
                       self._employee_repo, self._property_repo,
                       mode="add", on_save=self.refresh)

    def _edit(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showwarning("Выбор", "Выберите договор для редактирования.")
            return
        try:
            contract = self._repo.get_by_id(cid)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
            return
        ContractDialog(self, self._repo, self._client_repo,
                       self._employee_repo, self._property_repo,
                       mode="edit", entity=contract, on_save=self.refresh)

    def _delete(self):
        cid = self._selected_id()
        if cid is None:
            messagebox.showwarning("Выбор", "Выберите договор для удаления.")
            return
        if not messagebox.askyesno("Удаление", "Удалить выбранный договор?"):
            return
        try:
            self._repo.delete(cid)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить договор:\n{e}")


class ContractDialog(tk.Toplevel):
    """Модальный диалог добавления / редактирования договора."""

    def __init__(self, parent, repo: ContractRepository,
                 client_repo: ClientRepository,
                 employee_repo: EmployeeRepository,
                 property_repo: PropertyRepository,
                 mode: str, entity: Contract = None, on_save=None):
        super().__init__(parent)
        self._repo          = repo
        self._client_repo   = client_repo
        self._employee_repo = employee_repo
        self._property_repo = property_repo
        self._mode, self._entity, self._on_save = mode, entity, on_save
        self.title("Добавить договор" if mode == "add" else "Редактировать договор")
        self.resizable(False, False)
        self.grab_set()
        self._build()
        if entity:
            self._fill(entity)

    def _build(self):
        try:
            clients    = self._client_repo.get_all()
            employees  = self._employee_repo.get_all()
            properties = self._property_repo.get_all()
        except Exception:
            clients, employees, properties = [], [], []

        self._client_map   = {f"{c.last_name} {c.first_name} (ID {c.id})": c.id for c in clients}
        self._employee_map = {f"{e.last_name} {e.first_name} (ID {e.id})": e.id for e in employees}
        self._property_map = {f"{p.property_type} №{p.number} (ID {p.id})": p.id for p in properties}

        ttk.Label(self, text="Дата договора * (ГГГГ-ММ-ДД)").grid(
            row=0, column=0, sticky=tk.W, padx=8, pady=3)
        self._date_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._date_var, width=32).grid(
            row=0, column=1, padx=8, pady=3)

        ttk.Label(self, text="Сумма * (руб.)").grid(row=1, column=0, sticky=tk.W, padx=8, pady=3)
        self._amount_var = tk.StringVar()
        ttk.Entry(self, textvariable=self._amount_var, width=32).grid(
            row=1, column=1, padx=8, pady=3)

        ttk.Label(self, text="Статус *").grid(row=2, column=0, sticky=tk.W, padx=8, pady=3)
        self._status_var = tk.StringVar(value="оформлен")
        ttk.Combobox(self, textvariable=self._status_var,
                     values=["оформлен", "завершён", "расторгнут"],
                     state="readonly", width=30).grid(row=2, column=1, padx=8, pady=3)

        for row_idx, (label, attr, mapping) in enumerate([
            ("Клиент *",    "_client_var",   self._client_map),
            ("Сотрудник *", "_employee_var", self._employee_map),
            ("Объект *",    "_property_var", self._property_map),
        ], start=3):
            ttk.Label(self, text=label).grid(row=row_idx, column=0, sticky=tk.W, padx=8, pady=3)
            var = tk.StringVar()
            setattr(self, attr, var)
            ttk.Combobox(self, textvariable=var, values=list(mapping.keys()),
                         state="readonly", width=30).grid(row=row_idx, column=1, padx=8, pady=3)

        fb = ttk.Frame(self)
        fb.grid(row=6, column=0, columnspan=2, pady=8)
        ttk.Button(fb, text="Сохранить", command=self._save).pack(side=tk.LEFT, padx=6)
        ttk.Button(fb, text="Отмена",    command=self.destroy).pack(side=tk.LEFT, padx=6)

    def _fill(self, c: Contract):
        self._date_var.set(str(c.contract_date))
        self._amount_var.set(str(c.amount))
        self._status_var.set(c.status)
        for label, cid in self._client_map.items():
            if cid == c.client_id:
                self._client_var.set(label); break
        for label, eid in self._employee_map.items():
            if eid == c.employee_id:
                self._employee_var.set(label); break
        for label, pid in self._property_map.items():
            if pid == c.property_id:
                self._property_var.set(label); break

    def _save(self):
        date_s  = self._date_var.get().strip()
        amt_s   = self._amount_var.get().strip()
        cl_lbl  = self._client_var.get()
        em_lbl  = self._employee_var.get()
        pr_lbl  = self._property_var.get()
        if not (date_s and amt_s and cl_lbl and em_lbl and pr_lbl):
            messagebox.showerror("Ошибка", "Заполните все обязательные поля (*).")
            return
        try:
            amount = float(amt_s)
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Сумма должна быть положительным числом.")
            return
        try:
            if self._mode == "add":
                self._repo.create(Contract(
                    contract_date=date_s, amount=amount,
                    status=self._status_var.get(),
                    client_id=self._client_map[cl_lbl],
                    employee_id=self._employee_map[em_lbl],
                    property_id=self._property_map[pr_lbl],
                ))
            else:
                self._entity.contract_date = date_s
                self._entity.amount        = amount
                self._entity.status        = self._status_var.get()
                self._entity.client_id     = self._client_map[cl_lbl]
                self._entity.employee_id   = self._employee_map[em_lbl]
                self._entity.property_id   = self._property_map[pr_lbl]
                self._repo.update(self._entity)
            if self._on_save:
                self._on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить договор:\n{e}")


# ---------------------------------------------------------------------------
# Вкладка «Отчёты» — три под-вкладки, по одному отчёту на каждой
# ---------------------------------------------------------------------------

class ReportsTab(ttk.Frame):
    """Вкладка «Отчёты» с тремя под-страницами (вложенный Notebook).

    Каждый отчёт на своей вкладке, не мешает остальным.
    """

    def __init__(self, parent):
        super().__init__(parent)
        inner = ttk.Notebook(self)
        inner.pack(fill=tk.BOTH, expand=True)

        tab1 = _ContractReportTab(inner)
        tab2 = _DealsReportTab(inner)
        tab3 = _RevenueReportTab(inner)

        inner.add(tab1, text="  Договор купли-продажи  ")
        inner.add(tab2, text="  Реестр сделок по сотрудникам  ")
        inner.add(tab3, text="  Выручка по типам объектов  ")


class _ContractReportTab(ttk.Frame):
    """Отчёт по одному договору купли-продажи.

    Поле выбора договора поддерживает автодополнение:
    по мере ввода список сужается до подходящих договоров.
    """

    COLUMNS = ("client_name", "property_type", "area", "price", "contract_date", "status")
    HEADERS = ("ФИО клиента", "Тип объекта", "Площадь, м²", "Цена, руб.",
               "Дата договора", "Статус")

    def __init__(self, parent):
        super().__init__(parent)
        self._summaries: list[dict] = []
        self._options:   list[str]  = []
        self._id_map:    dict[str, int] = {}
        self._load_contracts()
        self._build()

    def _load_contracts(self):
        """Загружает список договоров из БД для автодополнения."""
        try:
            self._summaries = get_contract_summaries()
            self._options = [
                f"{s['id']} — {s['client']} — {s['contract_date']} — {s['amount']} руб."
                for s in self._summaries
            ]
            self._id_map = {
                opt: s["id"]
                for opt, s in zip(self._options, self._summaries)
            }
        except Exception:
            pass

    def _build(self):
        """Строит панель управления и Treeview."""
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(ctrl, text="Договор:").pack(side=tk.LEFT, padx=(0, 4))

        self._combo = _AutoCombo(ctrl, width=55)
        self._combo.load(self._options)
        self._combo.pack(side=tk.LEFT, padx=(0, 6))

        ttk.Button(ctrl, text="Обновить список",
                   command=self._reload).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Сформировать",
                   command=self._generate).pack(side=tk.LEFT, padx=6)
        # Enter в поле также запускает отчёт
        self._combo.bind("<Return>", lambda _: self._generate())

        self._tree = self._make_tree(COLUMNS=self.COLUMNS, HEADERS=self.HEADERS)

    def _make_tree(self, COLUMNS, HEADERS) -> ttk.Treeview:
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        tree = ttk.Treeview(frame, columns=COLUMNS, show="headings")
        for col, hdr in zip(COLUMNS, HEADERS):
            tree.heading(col, text=hdr)
            tree.column(col, width=160, anchor=tk.W)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        return tree

    def _reload(self):
        """Перезагружает список договоров из БД."""
        self._load_contracts()
        self._combo.load(self._options)

    def _generate(self):
        """Извлекает ID договора из выбранного элемента и строит отчёт."""
        selected = self._combo.get().strip()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите договор из списка или введите его номер.")
            return

        # Попытка 1: точное совпадение с опцией
        contract_id = self._id_map.get(selected)
        # Попытка 2: пользователь ввёл только число
        if contract_id is None:
            try:
                contract_id = int(selected.split(" ")[0])
            except ValueError:
                messagebox.showerror("Ошибка", "Не удалось определить номер договора.")
                return

        try:
            rows = sales_contract_report(contract_id)
            _clear_tree(self._tree)
            if not rows:
                messagebox.showinfo("Результат", f"Договор №{contract_id} не найден.")
                return
            for r in rows:
                self._tree.insert("", tk.END, values=(
                    r["client_name"], r["property_type"],
                    r["area"], r["price"],
                    r["contract_date"], r["status"],
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class _DealsReportTab(ttk.Frame):
    """Отчёт — реестр сделок по сотрудникам за период.

    Кнопка «Весь период» автоматически заполняет даты
    из минимального и максимального значений в таблице contracts.
    """

    COLUMNS = ("employee", "client", "property_type", "amount", "contract_date")
    HEADERS = ("Сотрудник", "Клиент", "Тип объекта", "Сумма, руб.", "Дата")

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(ctrl, text="Дата с:").pack(side=tk.LEFT, padx=(0, 4))
        self._from_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self._from_var, width=12).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(ctrl, text="по:").pack(side=tk.LEFT, padx=(0, 4))
        self._to_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self._to_var, width=12).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(ctrl, text="Весь период",
                   command=self._fill_period).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Сформировать",
                   command=self._generate).pack(side=tk.LEFT, padx=8)

        ttk.Label(ctrl, text="Формат: ГГГГ-ММ-ДД",
                  foreground="gray").pack(side=tk.LEFT, padx=4)

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings")
        for col, hdr in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=180, anchor=tk.W)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _fill_period(self):
        """Автозаполняет даты на основе крайних значений в БД."""
        try:
            min_d, max_d = get_date_range()
            self._from_var.set(min_d)
            self._to_var.set(max_d)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _generate(self):
        date_from = self._from_var.get().strip()
        date_to   = self._to_var.get().strip()
        if not (date_from and date_to):
            messagebox.showerror("Ошибка", "Введите начальную и конечную даты.")
            return
        try:
            rows = deals_by_employee_report(date_from, date_to)
            _clear_tree(self._tree)
            for r in rows:
                self._tree.insert("", tk.END, values=(
                    r["employee"], r["client"], r["property_type"],
                    r["amount"], r["contract_date"],
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class _RevenueReportTab(ttk.Frame):
    """Отчёт — выручка по типам объектов за период.

    Кнопка «Весь период» работает аналогично вкладке реестра сделок.
    """

    COLUMNS = ("property_type", "deal_count", "total_revenue")
    HEADERS = ("Тип объекта", "Количество сделок", "Общая выручка, руб.")

    def __init__(self, parent):
        super().__init__(parent)
        self._build()

    def _build(self):
        ctrl = ttk.Frame(self)
        ctrl.pack(fill=tk.X, padx=8, pady=8)

        ttk.Label(ctrl, text="Дата с:").pack(side=tk.LEFT, padx=(0, 4))
        self._from_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self._from_var, width=12).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(ctrl, text="по:").pack(side=tk.LEFT, padx=(0, 4))
        self._to_var = tk.StringVar()
        ttk.Entry(ctrl, textvariable=self._to_var, width=12).pack(side=tk.LEFT, padx=(0, 8))

        ttk.Button(ctrl, text="Весь период",
                   command=self._fill_period).pack(side=tk.LEFT, padx=2)
        ttk.Button(ctrl, text="Сформировать",
                   command=self._generate).pack(side=tk.LEFT, padx=8)

        ttk.Label(ctrl, text="Формат: ГГГГ-ММ-ДД",
                  foreground="gray").pack(side=tk.LEFT, padx=4)

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        self._tree = ttk.Treeview(frame, columns=self.COLUMNS, show="headings")
        for col, hdr in zip(self.COLUMNS, self.HEADERS):
            self._tree.heading(col, text=hdr)
            self._tree.column(col, width=220, anchor=tk.W)
        sb = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _fill_period(self):
        """Автозаполняет даты на основе крайних значений в БД."""
        try:
            min_d, max_d = get_date_range()
            self._from_var.set(min_d)
            self._to_var.set(max_d)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def _generate(self):
        date_from = self._from_var.get().strip()
        date_to   = self._to_var.get().strip()
        if not (date_from and date_to):
            messagebox.showerror("Ошибка", "Введите начальную и конечную даты.")
            return
        try:
            rows = revenue_by_property_type_report(date_from, date_to)
            _clear_tree(self._tree)
            for r in rows:
                self._tree.insert("", tk.END, values=(
                    r["property_type"], r["deal_count"], r["total_revenue"],
                ))
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
