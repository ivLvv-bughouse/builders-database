# План: БД для строительной компании (курсовая)

## Контекст
Курсовая работа по дисциплине "БД", 3 курс ГУАП. Нужна база данных для строительной компании с веб-клиентом. Стек: FastAPI + PostgreSQL + React. Проект на ранней стадии — все файлы пустые, есть скелет папок и venv.

## Сущности БД (7 таблиц + users)

1. **houses** — Дома (id, address, floors, construction_status, start_date, planned_end_date, actual_end_date)
2. **premises** — Помещения (id, house_id FK, type, number, floor, area, rooms_count, status)
3. **departments** — Отделы (id, name, description, head_id FK→employees)
4. **employees** — Сотрудники (id, full_name, department_id FK, position, phone, email, hire_date, salary, status)
5. **buyers** — Покупатели (id, full_name, phone, email, passport_series_number, registration_date)
6. **equity_agreements** — ДДУ (id, buyer_id FK, premise_id FK, agreement_date, price, status, registration_date)
7. **contractors** — Контрагенты (id, organization_name, inn, type, contact_person, phone, email, legal_address)
8. **users** — Пользователи системы (id, username, hashed_password, role, is_active)

---

## Этап 0: Инфраструктура и Docker

- [ ] `docker-compose.yml` — 3 сервиса: db (PostgreSQL 16), backend (FastAPI), frontend (React/Vite)
- [ ] `backend/Dockerfile` — python:3.12-slim, uvicorn с --reload
- [ ] `frontend/Dockerfile` — node:20-alpine, npm run dev
- [ ] `backend/.env` — DATABASE_URL, SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES

## Этап 1: Backend — подключение к БД и модели

**Файлы:** `backend/requirements.txt`, `app/config.py`, `app/database.py`, `app/models/*.py`

- [ ] `requirements.txt`:
  - **fastapi** — веб-фреймворк для REST API (автогенерация Swagger-документации, валидация, async)
  - **uvicorn** — ASGI-сервер для запуска FastAPI
  - **sqlalchemy** — ORM для работы с БД через Python-объекты вместо сырого SQL
  - **asyncpg** — асинхронный драйвер PostgreSQL (SQLAlchemy использует его под капотом)
  - **alembic** — миграции БД (версионирование схемы: добавил колонку → alembic создаёт SQL-скрипт)
  - **pydantic** — валидация входных/выходных данных API (автоматически проверяет типы, обязательность полей)
  - **pydantic-settings** — чтение конфигурации из .env файла в типизированный объект Settings
  - **python-jose** — генерация и проверка JWT-токенов для авторизации
  - **passlib[bcrypt]** — безопасное хэширование паролей (bcrypt)
  - **python-dotenv** — загрузка переменных окружения из .env
  - **python-multipart** — парсинг form-data (нужен для формы логина OAuth2)
- [ ] `app/config.py` — Settings (BaseSettings из pydantic-settings)
- [ ] `app/database.py` — async engine, async session, Base, get_db dependency
- [ ] SQLAlchemy-модели (7 таблиц + users) в `app/models/`
- [ ] Alembic: init, настроить async env.py, первая миграция
- [ ] `main.py` — создать FastAPI app, CORS middleware, подключение роутеров

**Архитектурные решения:**
- Async SQLAlchemy + asyncpg
- Enum-поля как VARCHAR, валидация через Pydantic Literal
- head_id в departments — nullable, use_alter=True (циклическая FK)

## Этап 2: Pydantic-схемы

**Файлы:** `app/schemas/*.py`

- [ ] Для каждой сущности: Base, Create, Update (Optional поля), Response (from_attributes), Filter

## Этап 3: CRUD-роутеры

**Файлы:** `app/routers/*.py`

Порядок (по зависимостям FK):
1. departments
2. employees (→ departments)
3. houses
4. premises (→ houses)
5. buyers
6. contractors
7. equity_agreements (→ buyers, premises)

Каждый роутер — 5 endpoints:
- `GET /api/<entities>` — список + пагинация (skip/limit) + фильтры
- `GET /api/<entities>/{id}`
- `POST /api/<entities>`
- `PUT /api/<entities>/{id}`
- `DELETE /api/<entities>/{id}`

## Этап 4: Авторизация (JWT)

**Файлы:** `app/auth/jwt.py`, `app/auth/dependencies.py`, `app/auth/password.py`, `app/routers/auth.py`

- [ ] Хэширование паролей (bcrypt)
- [ ] Генерация/валидация JWT (python-jose)
- [ ] Dependencies: get_current_user, require_admin
- [ ] Endpoints: POST /api/auth/login, POST /api/auth/register, GET /api/auth/me
- [ ] Роли: admin (полный CRUD), user (только чтение)
- [ ] Скрипт создания начального admin-пользователя

## Этап 5: Отчёты (backend)

**Файлы:** `app/routers/reports.py`, `app/services/reports.py`

- [ ] Статусы строительства — кол-во домов по статусам, просроченные
- [ ] Продажи помещений — кол-во по статусам, сумма ДДУ по домам, средняя цена за м²
- [ ] Кадровый отчёт — сотрудники по отделам, средняя зарплата, ФОТ

## Этап 6: Frontend — каркас

- [ ] Инициализация Vite + React + TypeScript
- [ ] Зависимости: react-router-dom, axios, @mui/material, @mui/icons-material, @emotion/react, @emotion/styled, @mui/x-data-grid, recharts
- [ ] `api/client.ts` — Axios instance + JWT interceptor
- [ ] Layout: Sidebar (навигация) + Header (пользователь, выход)
- [ ] React Router в App.tsx
- [ ] AuthContext — хранение токена, login/logout

## Этап 7: Frontend — CRUD-страницы

Для каждой из 7 сущностей:
- [ ] Таблица (MUI DataGrid) с пагинацией, сортировкой, поиском
- [ ] Модалка создания/редактирования
- [ ] Диалог подтверждения удаления
- [ ] Фильтры

Порядок: Login → Dashboard → Houses → Premises → Departments → Employees → Buyers → Contractors → EquityAgreements

## Этап 8: Frontend — отчёты и дашборд

- [ ] DashboardPage — карточки-виджеты (всего домов, помещений, ДДУ и т.д.)
- [ ] ReportsPage с вкладками (MUI Tabs) + графики (Recharts)

## Этап 9: Тестирование и seed-данные

- [ ] pytest + httpx: тесты CRUD, авторизации, отчётов
- [ ] `app/seed.py` — заполнение БД тестовыми данными (5 домов, 30 помещений, 15 сотрудников и т.д.)
- [ ] Ручное тестирование через Swagger UI (/docs) и фронтенд

## Этап 10: Финальная сборка

- [ ] `docker-compose up --build` поднимает всё с нуля
- [ ] Alembic-миграции в entrypoint backend-контейнера
- [ ] README.md с инструкцией запуска

---

## Структура проекта (целевая)

```
backend/
  Dockerfile
  .env
  requirements.txt
  alembic.ini
  alembic/env.py, versions/
  main.py
  app/
    config.py
    database.py
    models/    (house, premise, employee, department, buyer, equity_agreement, contractor, user)
    schemas/   (аналогично + report)
    routers/   (аналогично + auth, reports)
    services/  (reports.py)
    auth/      (jwt.py, dependencies.py, password.py)
    seed.py

frontend/
  Dockerfile
  package.json, vite.config.ts
  src/
    main.tsx, App.tsx
    api/       (client.ts + по модулю на сущность)
    components/ (layout/, common/, по сущности/, reports/, auth/)
    pages/     (по странице на сущность + Dashboard, Reports, Login)
    context/   (AuthContext.tsx)
    hooks/     (useAuth.ts)
    types/     (index.ts)
```

## Верификация
1. `docker-compose up --build` — всё поднимается без ошибок
2. Swagger UI на localhost:8000/docs — все endpoints работают
3. Фронтенд на localhost:5173 — логин, CRUD по всем таблицам, отчёты
4. pytest — все тесты проходят
