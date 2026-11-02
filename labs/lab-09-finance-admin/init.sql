-- Dados fictícios: pedidos cancelados, candidatos a bônus de retenção.
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    customer TEXT NOT NULL,
    total NUMERIC(10, 2) NOT NULL,
    status TEXT NOT NULL,
    cancel_reason TEXT
);
CREATE TABLE retention_bonuses (
    order_id INTEGER PRIMARY KEY REFERENCES orders (id),
    amount NUMERIC(10, 2) NOT NULL,
    granted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
INSERT INTO orders VALUES
    (1, 'Ana', 120.00, 'delivered', NULL),
    (2, 'Bruno', 350.00, 'canceled', 'logistics'),
    (3, 'Carla', 89.90, 'canceled', 'price');
