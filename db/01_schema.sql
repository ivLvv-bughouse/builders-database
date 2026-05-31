-- Схема базы данных строительной компании
-- Порядок создания таблиц соблюдает зависимости внешних ключей

-- Таблица клиентов: физические и юридические лица, покупающие объекты
CREATE TABLE clients (
    id          SERIAL PRIMARY KEY,
    last_name   VARCHAR NOT NULL,
    first_name  VARCHAR NOT NULL,
    middle_name VARCHAR,
    phone       VARCHAR NOT NULL UNIQUE,
    email       VARCHAR,
    passport    VARCHAR NOT NULL UNIQUE,
    client_type VARCHAR NOT NULL CHECK (client_type IN ('физ. лицо', 'юр. лицо'))
);

-- Таблица сотрудников: менеджеры и агенты, оформляющие договоры
CREATE TABLE employees (
    id          SERIAL PRIMARY KEY,
    last_name   VARCHAR NOT NULL,
    first_name  VARCHAR NOT NULL,
    middle_name VARCHAR,
    position    VARCHAR NOT NULL,
    phone       VARCHAR NOT NULL,
    salary      DECIMAL NOT NULL CHECK (salary > 0)
);

-- Таблица зданий: жилые и коммерческие комплексы компании
CREATE TABLE buildings (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR NOT NULL,
    address          VARCHAR NOT NULL UNIQUE,
    floors           INT NOT NULL CHECK (floors > 0),
    completion_date  DATE NOT NULL
);

-- Таблица объектов: квартиры, паркоместа и коммерческие помещения в зданиях
CREATE TABLE properties (
    id            SERIAL PRIMARY KEY,
    property_type VARCHAR NOT NULL CHECK (property_type IN ('квартира', 'паркоместо', 'коммерческое')),
    number        VARCHAR NOT NULL,
    area          DECIMAL NOT NULL CHECK (area > 0),
    price         DECIMAL NOT NULL CHECK (price > 0),
    status        VARCHAR NOT NULL CHECK (status IN ('свободен', 'забронирован', 'продан')),
    building_id   INT NOT NULL REFERENCES buildings(id)
);

-- Таблица договоров: сделки купли-продажи между клиентами и компанией
CREATE TABLE contracts (
    id            SERIAL PRIMARY KEY,
    contract_date DATE NOT NULL,
    amount        DECIMAL NOT NULL CHECK (amount > 0),
    status        VARCHAR NOT NULL CHECK (status IN ('оформлен', 'завершён', 'расторгнут')),
    client_id     INT NOT NULL REFERENCES clients(id),
    employee_id   INT NOT NULL REFERENCES employees(id),
    property_id   INT NOT NULL REFERENCES properties(id)
);
