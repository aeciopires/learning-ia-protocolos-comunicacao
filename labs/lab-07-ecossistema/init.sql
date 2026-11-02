-- Dados fictícios para o cenário de pedidos.
CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers (id),
    status TEXT NOT NULL,
    total NUMERIC(10, 2) NOT NULL
);
INSERT INTO customers VALUES (1, 'Ana'), (2, 'Bruno'), (3, 'Carla');
INSERT INTO orders VALUES
    (1, 1, 'shipped', 120.00),
    (2, 2, 'payment_failed', 350.00),
    (3, 3, 'payment_failed', 89.90),
    (4, 1, 'processing', 45.50);

-- Papel somente leitura: o server não precisa de permissão de escrita para o que oferece.
CREATE ROLE catalog_reader NOLOGIN;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO catalog_reader;
