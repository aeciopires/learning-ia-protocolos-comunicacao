-- Dados fictícios para o cenário de pedidos.
CREATE TABLE orders (id TEXT PRIMARY KEY, status TEXT NOT NULL);
INSERT INTO orders VALUES ('A1', 'shipped'), ('A2', 'delayed'), ('A3', 'processing'), ('A4', 'delivered'), ('A5', 'canceled');
