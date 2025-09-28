-- Complete PostgreSQL Schema for Rice Market AirTable Database
-- Generated: 2025-09-27T07:41:34.594737
-- This schema includes both discovered and documented fields

-- Lookup table for commodity types (referenced by multiple tables)
CREATE TABLE IF NOT EXISTS commodities (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table: Contracts (Hợp Đồng)
CREATE TABLE IF NOT EXISTS contracts_hợp_đồng (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    received_quantity INTEGER,
    quantity_received_at_dn INTEGER,
    loss INTEGER,
    total_amount INTEGER,
    contract_date DATE,
    contract_number VARCHAR(50),
    customer INTEGER REFERENCES customers(id),
    quantity_kg INTEGER,
    entry_date DATE,
    voucher_number VARCHAR(50),
    commodity_type INTEGER REFERENCES commodities(id),
    unit_price DECIMAL(10,2),
    transport_cost DECIMAL(10,2),
    total_price_incl__transport DECIMAL(10,2),
    protein DECIMAL(5,2),
    ash DECIMAL(5,2),
    fibre DECIMAL(5,2),
    fat DECIMAL(5,2),
    moisture DECIMAL(5,2),
    starch DECIMAL(5,2),
    acid_value DECIMAL(5,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contracts_hợp_đồng_customer ON contracts_hợp_đồng(customer);
CREATE INDEX idx_contracts_hợp_đồng_commodity_type ON contracts_hợp_đồng(commodity_type);

-- Table: Contracts (Hợp Đồng) - 2
CREATE TABLE IF NOT EXISTS contracts_hợp_đồng___2 (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    receipt_date VARCHAR(255),
    receipt_number VARCHAR(255),
    unit_price INTEGER,
    logistics_cost_vc INTEGER,
    total_price_with_vc INTEGER,
    received_quantity INTEGER,
    imported_quantity_đn INTEGER,
    loss INTEGER,
    total_value INTEGER,
    protein_pct DECIMAL(15,4),
    ash_pct DECIMAL(15,4),
    fibre_pct DECIMAL(15,4),
    fat_pct DECIMAL(15,4),
    moisture_pct DECIMAL(15,4),
    starch_pct DECIMAL(15,4),
    acid_value_pct INTEGER,
    contract_date DATE,
    contract_number VARCHAR(50),
    customer INTEGER REFERENCES customers(id),
    quantity_kg INTEGER,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_contracts_hợp_đồng___2_customer ON contracts_hợp_đồng___2(customer);

-- Table: Customers
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    customer_name VARCHAR(255),
    national_id_cccd VARCHAR(255),
    address VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Table: Shipments
CREATE TABLE IF NOT EXISTS shipments (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    vehicle_container_number VARCHAR(255),
    delivered_quantity_kg INTEGER,
    arrival_time VARCHAR(255),
    shipment_date DATE,
    customer INTEGER REFERENCES customers(id),
    contract_number INTEGER REFERENCES contracts_hp_ng(id),
    contract_quantity INTEGER,
    unloading_date VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_shipments_customer ON shipments(customer);
CREATE INDEX idx_shipments_contract_number ON shipments(contract_number);

-- Table: Inventory Movements
CREATE TABLE IF NOT EXISTS inventory_movements (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    date DATE,
    batch_note VARCHAR(255),
    vehicle_container VARCHAR(255),
    ldh_kh VARCHAR(255),
    production_out_tons INTEGER,
    loss_1_3pct_from_1_6_2025 INTEGER,
    customer INTEGER REFERENCES customers(id),
    opening_balance_tons DECIMAL(10,2),
    quantity_received_tons DECIMAL(10,2),
    internal_transfer_out_tons DECIMAL(10,2),
    recovered_finished_goods_in_tons DECIMAL(10,2),
    domestic_sales_out_tons DECIMAL(10,2),
    raw_material_sales_out_tons DECIMAL(10,2),
    closing_balance_tons DECIMAL(10,2),
    fat_pct DECIMAL(5,2),
    moisture_pct DECIMAL(5,2),
    starch DECIMAL(5,2),
    acid_value DECIMAL(5,2),
    related_contract INTEGER REFERENCES contracts_hp_ng(id),
    related_shipment INTEGER REFERENCES shipments(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_inventory_movements_customer ON inventory_movements(customer);
CREATE INDEX idx_inventory_movements_related_contract ON inventory_movements(related_contract);
CREATE INDEX idx_inventory_movements_related_shipment ON inventory_movements(related_shipment);

-- Table: Finished Goods
CREATE TABLE IF NOT EXISTS finished_goods (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    ngày_nhập VARCHAR(255),
    ldh VARCHAR(255),
    máy VARCHAR(255),
    số_lượng_container INTEGER,
    số_lượng_theo_đầu_bao___trong_giờ DECIMAL(15,4),
    số_lượng_theo_đầu_bao___ngoài_giờ DECIMAL(15,4),
    tiền_bồi_dưỡng_bx_cont_50k_20t_100k_40t INTEGER,
    tiền_bx_trong_giờ_23k DECIMAL(15,4),
    ngoài_giờ DECIMAL(15,4),
    tổng_ca_1 DECIMAL(15,4),
    khách_hàng INTEGER,
    sản_xuất_tổng_giờ INTEGER,
    n16h30_19h INTEGER,
    n19h_7h INTEGER,
    mì VARCHAR(50),
    số_lượng_container_ca_2 INTEGER,
    số_lượng_theo_đầu_bao___trong_giờ_ca_2 DECIMAL(10,2),
    số_lượng_theo_đầu_bao___ngoài_giờ_ca_2 DECIMAL(10,2),
    tiền_bồi_dưỡng_bx_cont_ca_2 DECIMAL(10,2),
    tiền_bx_trong_giờ_ca_2 DECIMAL(10,2),
    ngoài_giờ_ca_2 DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_finished_goods_khách_hàng ON finished_goods(khách_hàng);

-- Junction tables for many-to-many relationships
CREATE TABLE IF NOT EXISTS contracts_hợp_đồng_related_shipments_junction (
    contracts_hợp_đồng_id INTEGER REFERENCES contracts_hợp_đồng(id) ON DELETE CASCADE,
    shipments_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    PRIMARY KEY (contracts_hợp_đồng_id, shipments_id)
);

CREATE TABLE IF NOT EXISTS contracts_hợp_đồng_related_inventory_movements_junction (
    contracts_hợp_đồng_id INTEGER REFERENCES contracts_hợp_đồng(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    PRIMARY KEY (contracts_hợp_đồng_id, inventory_movements_id)
);

CREATE TABLE IF NOT EXISTS contracts_hợp_đồng_price_lists_junction (
    contracts_hợp_đồng_id INTEGER REFERENCES contracts_hợp_đồng(id) ON DELETE CASCADE,
    price_lists_id INTEGER REFERENCES price_lists(id) ON DELETE CASCADE,
    PRIMARY KEY (contracts_hợp_đồng_id, price_lists_id)
);

CREATE TABLE IF NOT EXISTS contracts_hợp_đồng___2_commodity_type_junction (
    contracts_hợp_đồng___2_id INTEGER REFERENCES contracts_hợp_đồng___2(id) ON DELETE CASCADE,
    commodities_id INTEGER REFERENCES commodities(id) ON DELETE CASCADE,
    PRIMARY KEY (contracts_hợp_đồng___2_id, commodities_id)
);

CREATE TABLE IF NOT EXISTS contracts_hợp_đồng___2_related_inventory_movements_junction (
    contracts_hợp_đồng___2_id INTEGER REFERENCES contracts_hợp_đồng___2(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    PRIMARY KEY (contracts_hợp_đồng___2_id, inventory_movements_id)
);

CREATE TABLE IF NOT EXISTS customers_contracts_junction (
    customers_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    PRIMARY KEY (customers_id, contracts_hp_ng_id)
);

CREATE TABLE IF NOT EXISTS customers_shipments_junction (
    customers_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    shipments_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    PRIMARY KEY (customers_id, shipments_id)
);

CREATE TABLE IF NOT EXISTS customers_inventory_movements_junction (
    customers_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    PRIMARY KEY (customers_id, inventory_movements_id)
);

CREATE TABLE IF NOT EXISTS customers_finished_goods_junction (
    customers_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    finished_goods_id INTEGER REFERENCES finished_goods(id) ON DELETE CASCADE,
    PRIMARY KEY (customers_id, finished_goods_id)
);

CREATE TABLE IF NOT EXISTS customers_contracts_hợp_đồng___2_junction (
    customers_id INTEGER REFERENCES customers(id) ON DELETE CASCADE,
    contracts_hp_ng_2_id INTEGER REFERENCES contracts_hp_ng_2(id) ON DELETE CASCADE,
    PRIMARY KEY (customers_id, contracts_hp_ng_2_id)
);

CREATE TABLE IF NOT EXISTS shipments_commodity_type_junction (
    shipments_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    commodities_id INTEGER REFERENCES commodities(id) ON DELETE CASCADE,
    PRIMARY KEY (shipments_id, commodities_id)
);

CREATE TABLE IF NOT EXISTS shipments_inventory_movements_junction (
    shipments_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    PRIMARY KEY (shipments_id, inventory_movements_id)
);

CREATE TABLE IF NOT EXISTS shipments_contracts_hợp_đồng___2_junction (
    shipments_id INTEGER REFERENCES shipments(id) ON DELETE CASCADE,
    contracts_hp_ng_2_id INTEGER REFERENCES contracts_hp_ng_2(id) ON DELETE CASCADE,
    PRIMARY KEY (shipments_id, contracts_hp_ng_2_id)
);

CREATE TABLE IF NOT EXISTS inventory_movements_commodity_type_junction (
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    commodities_id INTEGER REFERENCES commodities(id) ON DELETE CASCADE,
    PRIMARY KEY (inventory_movements_id, commodities_id)
);

CREATE TABLE IF NOT EXISTS inventory_movements_contracts_hợp_đồng___2_junction (
    inventory_movements_id INTEGER REFERENCES inventory_movements(id) ON DELETE CASCADE,
    contracts_hp_ng_2_id INTEGER REFERENCES contracts_hp_ng_2(id) ON DELETE CASCADE,
    PRIMARY KEY (inventory_movements_id, contracts_hp_ng_2_id)
);
