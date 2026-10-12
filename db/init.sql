BEGIN;
CREATE TABLE products (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL CHECK (length(trim(name)) > 0),
    quantity INTEGER NOT NULL CHECK (quantity BETWEEN 0 AND 1000000),
    daily_usage INTEGER NOT NULL CHECK (daily_usage BETWEEN 1 AND 10000),
    lead_days INTEGER NOT NULL CHECK (lead_days BETWEEN 1 AND 365),
    safety_stock INTEGER NOT NULL CHECK (safety_stock BETWEEN 0 AND 1000000)
);
CREATE TABLE analyses (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    result JSONB NOT NULL
);
INSERT INTO products (name, quantity, daily_usage, lead_days, safety_stock) VALUES
 ('USB-C кабель', 12, 5, 3, 5),
 ('Блок питания 65W', 40, 2, 5, 5),
 ('Беспроводная мышь', 10, 3, 2, 4);
COMMIT;
