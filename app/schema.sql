CREATE TABLE IF NOT EXISTS kennels (
    id         SERIAL PRIMARY KEY,
    number     VARCHAR(20)  NOT NULL UNIQUE,
    capacity   INTEGER      NOT NULL DEFAULT 1 CHECK (capacity > 0),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS dogs (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    breed      VARCHAR(100) NOT NULL DEFAULT '',
    age        INTEGER      CHECK (age IS NULL OR age >= 0),
    kennel_id  INTEGER      REFERENCES kennels (id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS helpers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    phone      VARCHAR(30)  NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ  NOT NULL DEFAULT now()
);

-- Прогулки — история; собаку или помощника с прогулками удалить нельзя (RESTRICT).
CREATE TABLE IF NOT EXISTS walks (
    id         SERIAL PRIMARY KEY,
    dog_id     INTEGER     NOT NULL REFERENCES dogs (id) ON DELETE RESTRICT,
    helper_id  INTEGER     NOT NULL REFERENCES helpers (id) ON DELETE RESTRICT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at   TIMESTAMPTZ,
    CONSTRAINT walks_time_order CHECK (ended_at IS NULL OR ended_at > started_at)
);

CREATE INDEX IF NOT EXISTS walks_dog_idx    ON walks (dog_id);
CREATE INDEX IF NOT EXISTS walks_helper_idx ON walks (helper_id);
CREATE INDEX IF NOT EXISTS dogs_kennel_idx  ON dogs (kennel_id);
