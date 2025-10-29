-- Create tables for rice market database
CREATE TABLE IF NOT EXISTS inventory_data (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(100),
    quantity DECIMAL(10,2),
    price DECIMAL(10,2),
    date DATE,
    supplier_id INTEGER
);

CREATE TABLE IF NOT EXISTS suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200),
    contact VARCHAR(100),
    address TEXT,
    rating DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),
    amount DECIMAL(10,2),
    date DATE,
    item_id INTEGER,
    supplier_id INTEGER
);

CREATE TABLE IF NOT EXISTS price_history (
    id SERIAL PRIMARY KEY,
    item_type VARCHAR(100),
    price DECIMAL(10,2),
    date DATE,
    market_conditions TEXT
);

-- Insert sample data
INSERT INTO inventory_data (item_type, quantity, price, date, supplier_id) VALUES
('Basmati Rice', 500, 45.50, '2024-10-01', 1),
('Jasmine Rice', 300, 42.00, '2024-10-01', 2),
('Brown Rice', 200, 38.50, '2024-10-01', 1);

INSERT INTO suppliers (name, contact, address, rating) VALUES
('Rice Suppliers Inc', 'contact@ricesuppliers.com', '123 Market St', 4.5),
('Global Rice Co', 'info@globalrice.com', '456 Trade Ave', 4.2);
