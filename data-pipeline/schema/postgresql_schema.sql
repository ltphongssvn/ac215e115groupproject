-- PostgreSQL Schema for AirTable Base: appmeTyHLozoqighD
-- Generated: 2025-09-27T00:54:01.041926

CREATE TABLE IF NOT EXISTS Contracts_Hợp_Đồng (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    received_quantity INTEGER,
    quantity_received_at_dn INTEGER,
    loss INTEGER,
    total_amount INTEGER
);

CREATE TABLE IF NOT EXISTS Contracts_Hợp_Đồng___2 (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    receipt_date VARCHAR(255),
    receipt_number VARCHAR(255),
    commodity_type INTEGER[],
    unit_price INTEGER,
    logistics_cost_vc INTEGER,
    total_price_with_vc INTEGER,
    received_quantity INTEGER,
    imported_quantity_đn INTEGER,
    loss INTEGER,
    total_value INTEGER,
    protein_% DECIMAL(15,4),
    ash_% DECIMAL(15,4),
    fibre_% DECIMAL(15,4),
    fat_% DECIMAL(15,4),
    moisture_% DECIMAL(15,4),
    starch_% DECIMAL(15,4),
    acid_value_% INTEGER
);

CREATE TABLE IF NOT EXISTS Customers (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    customer_name VARCHAR(255),
    national_id_cccd VARCHAR(255),
    address VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Shipments (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    commodity_type INTEGER[],
    vehicle/container_number VARCHAR(255),
    delivered_quantity_kg INTEGER,
    arrival_time VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Inventory_Movements (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    date DATE,
    batch/note VARCHAR(255),
    vehicle/container VARCHAR(255),
    ldh/kh VARCHAR(255),
    commodity_type INTEGER[],
    production_out_tons INTEGER,
    loss_1.3%_from_1/6/2025 INTEGER
);

CREATE TABLE IF NOT EXISTS Finished_Goods (
    id SERIAL PRIMARY KEY,
    airtable_id VARCHAR(20) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ngày_nhập VARCHAR(255),
    ldh VARCHAR(255),
    máy VARCHAR(255),
    số_lượng_container INTEGER,
    số_lượng_theo_đầu_bao_-_trong_giờ DECIMAL(15,4),
    số_lượng_theo_đầu_bao_-_ngoài_giờ DECIMAL(15,4),
    tiền_bồi_dưỡng_bx_cont_50k/20t,_100k/40t INTEGER,
    tiền_bx_trong_giờ_23k DECIMAL(15,4),
    ngoài_giờ DECIMAL(15,4),
    tổng_ca_1 DECIMAL(15,4)
);
