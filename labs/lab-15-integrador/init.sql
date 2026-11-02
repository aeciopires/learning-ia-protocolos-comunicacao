-- Dados fictícios do assistente de pós-venda.
CREATE TABLE orders (id INTEGER PRIMARY KEY, customer TEXT NOT NULL, status TEXT NOT NULL, total NUMERIC(10, 2) NOT NULL);
CREATE TABLE policies (topic TEXT PRIMARY KEY, body TEXT NOT NULL);
INSERT INTO orders VALUES (1, 'Ana', 'delivered', 120.00), (2, 'Bruno', 'delayed', 350.00);
INSERT INTO policies VALUES ('delay', 'Delayed orders may receive a bonus of up to 20% of the total.');
