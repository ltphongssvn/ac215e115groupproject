-- PostgreSQL DDL for AirTable Base: appmeTyHLozoqighD
-- Generated: 2025-10-01T19:07:04.462456
-- Source: AirTable API Documentation Parser v2
--
-- This database schema replicates the structure of your AirTable base
-- with the following considerations:
-- 1. AirTable record IDs are preserved in 'airtable_record_id' columns
-- 2. Relationships are maintained using foreign keys and junction tables
-- 3. All tables include created_at and updated_at timestamps
-- 4. Indexes are created on foreign key columns for query performance
--
-- Tables included: 8 tables
-- Total fields: 195 fields
-- Relationships: 35 relationships

-- ============================================================

-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS airtable_sync;

-- Set search path to include our schema
SET search_path TO airtable_sync, public;

-- Enable useful extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";  -- For generating UUIDs
CREATE EXTENSION IF NOT EXISTS "btree_gist";  -- For exclusion constraints


-- Table: Contracts (Hợp Đồng) (AirTable ID: tbl7sHbwOCOTjL2MC)
CREATE TABLE IF NOT EXISTS contracts_hp_ng (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    contract_date DATE,
    contract_number TEXT,
    quantity_kg INTEGER,
    entry_date DATE,
    voucher_number TEXT,
    unit_price DECIMAL(15,2),
    transport_cost DECIMAL(15,2),
    total_price_incl__transport DECIMAL(15,2),
    received_quantity INTEGER,
    quantity_received_at_dn INTEGER,
    loss INTEGER,
    total_amount DECIMAL(15,2),
    protein INTEGER,
    ash INTEGER,
    fibre INTEGER,
    fat INTEGER,
    moisture INTEGER,
    starch INTEGER,
    acid_value INTEGER,
    notes TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE contracts_hp_ng IS 'Contracts (Hợp Đồng) data synchronized from AirTable';


-- Table: Contracts (Hợp Đồng) - 2 (AirTable ID: tbllz4cazITSwnXIo)
CREATE TABLE IF NOT EXISTS contracts_hp_ng___2 (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    contract_date DATE,
    contract_number TEXT,
    quantity_kg INTEGER,
    receipt_date TEXT,
    receipt_number TEXT,
    unit_price DECIMAL(15,2),
    logistics_cost_vc INTEGER,
    total_price_with_vc DECIMAL(15,2),
    received_quantity INTEGER,
    imported_quantity_n INTEGER,
    loss INTEGER,
    total_value DECIMAL(15,2),
    protein_pct DECIMAL(5,3),
    ash_pct DECIMAL(5,3),
    fibre_pct DECIMAL(5,3),
    fat_pct DECIMAL(5,3),
    moisture_pct DECIMAL(5,3),
    starch_pct DECIMAL(5,3),
    acid_value_pct DECIMAL(5,3),
    notes TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE contracts_hp_ng___2 IS 'Contracts (Hợp Đồng) - 2 data synchronized from AirTable';


-- Table: Customers (AirTable ID: tblDUfIlNy07Z0hiL)
CREATE TABLE IF NOT EXISTS customers (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    customer_name TEXT,
    national_id_cccd TEXT,
    address TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE customers IS 'Customers data synchronized from AirTable';


-- Table: Shipments (AirTable ID: tblSj7JcxYYfs6Dcl)
CREATE TABLE IF NOT EXISTS shipments (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    shipment_date DATE,
    vehicle_container_number TEXT,
    contract_quantity INTEGER,
    delivered_quantity_kg INTEGER,
    arrival_time TEXT,
    unloading_date TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE shipments IS 'Shipments data synchronized from AirTable';


-- Table: Inventory Movements (AirTable ID: tblhb3Vxhi6Yt0BDw)
CREATE TABLE IF NOT EXISTS inventory_movements (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    date DATE,
    batch_note TEXT,
    vehicle_container TEXT,
    ldh_kh TEXT,
    opening_balance_tons DECIMAL(15,4),
    quantity_received_tons DECIMAL(15,4),
    internal_transfer_out_tons DECIMAL(15,4),
    recovered_finished_goods_in_tons DECIMAL(15,4),
    domestic_sales_out_tons DECIMAL(15,4),
    production_out_tons DECIMAL(15,4),
    loss_1_3pct_from_1_6_2025 DECIMAL(15,4),
    raw_material_sales_out_tons DECIMAL(15,4),
    closing_balance_tons DECIMAL(15,4),
    bx_a__chin TEXT,
    bx_ngoi_ni TEXT,
    bx_tr TEXT,
    bx_ti TEXT,
    bx_a_dng TEXT,
    bx___thoa TEXT,
    fat_pct DECIMAL(5,3),
    moisture_pct DECIMAL(5,3),
    starch DECIMAL(15,4),
    acid_value DECIMAL(15,4),
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE inventory_movements IS 'Inventory Movements data synchronized from AirTable';


-- Table: Finished Goods (AirTable ID: tblNY26FnHswHRcWS)
CREATE TABLE IF NOT EXISTS finished_goods (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    ngy_nhp TEXT,
    ldh TEXT,
    my TEXT,
    sn_xut_tng_gi INTEGER,
    n_16h30_19h INTEGER,
    n_19h_7h INTEGER,
    m TEXT,
    s_lng_container INTEGER,
    s_lng_theo_u_bao___trong_gi INTEGER,
    s_lng_theo_u_bao___ngoi_gi INTEGER,
    tin_bi_dng_bx_cont_50k_20t_100k_40t DECIMAL(15,2),
    tin_bx_trong_gi_23k DECIMAL(15,2),
    ngoi_gi DECIMAL(15,2),
    tng_ca_1 DECIMAL(15,2),
    s_lng_container_ca_2 INTEGER,
    s_lng_theo_u_bao___trong_gi_ca_2 INTEGER,
    s_lng_theo_u_bao___ngoi_gi_ca_2 INTEGER,
    tin_bi_dng_bx_cont_ca_2 DECIMAL(15,2),
    tin_bx_trong_gi_ca_2 DECIMAL(15,2),
    ngoi_gi_ca_2 DECIMAL(15,2),
    tng_ca_2 DECIMAL(15,2),
    ngy_k_bx_ca_1 TEXT,
    trong_gi_57k_ca_1 DECIMAL(15,2),
    ngoi_gi_75k__ch_nht_ca_1 DECIMAL(15,2),
    ngoi_gi_87k_19_7h_l_cn_ca_m_ca_1 DECIMAL(15,2),
    m_p_ca_1 INTEGER,
    ngy_l_5715_ca_1 DECIMAL(15,2),
    bi_dng_xp_bao_ngy_ca_1 DECIMAL(15,2),
    tng_ca_1_bx DECIMAL(15,2),
    ngy_k_bx_ca_2 TEXT,
    trong_gi_57k_ca_2 DECIMAL(15,2),
    ngoi_gi_72k_ca_2 DECIMAL(15,2),
    ngoi_gi_87k_19_7h_l_cn_ca_m_ca_2 DECIMAL(15,2),
    la_m_trong_gi_ca_2 INTEGER,
    la_m_ngoi_gi_ca_2 INTEGER,
    ngy_l_5715_ca_2 DECIMAL(15,2),
    bi_dng_dn_bao_200k_ngy_ca_2 DECIMAL(15,2),
    tng_ca_2_bx DECIMAL(15,2),
    ngy_k_bx_ca_3 DATE,
    trong_gi_57k_ca_3 DECIMAL(15,2),
    ngoi_gi_76k_ca_3 DECIMAL(15,2),
    ngoi_gi_87k_19_7h_l_cn_ca_m_ca_3 DECIMAL(15,2),
    la_m_trong_gi_ca_3 INTEGER,
    la_m_ngoi_gi_ca_3 INTEGER,
    ngy_l_5715_ca_3 DECIMAL(15,2),
    bi_dng_dn_bao_200k_ngy_ca_3 DECIMAL(15,2),
    tng_ca_3_bx DECIMAL(15,2),
    ngy_k_bx_ca_4 DATE,
    trong_gi_57k_ca_4 DECIMAL(15,2),
    ngoi_gi_75k__ch_nht_ca_4 DECIMAL(15,2),
    ngoi_gi_87k_19_7h_l_cn_ca_m_ca_4 DECIMAL(15,2),
    m_p_ca_4 INTEGER,
    ngy_l_5715_ca_4 DECIMAL(15,2),
    bi_dng_xp_bao_ngy_ca_4 DECIMAL(15,2),
    tng_ca_4_bx DECIMAL(15,2),
    ngy_k_bx_ca_5 DATE,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE finished_goods IS 'Finished Goods data synchronized from AirTable';


-- Table: Commodities (AirTable ID: tblawXefYSXa6UFSX)
CREATE TABLE IF NOT EXISTS commodities (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    commodity_name TEXT,
    commodity_photo TEXT,
    commodity_type VARCHAR(100),
    description TEXT,
    number_of_contracts TEXT,
    total_contracted_quantity_kg TEXT,
    average_unit_price_from_contracts TEXT,
    total_shipments TEXT,
    total_inventory_movements TEXT,
    total_finished_goods_records TEXT,
    latest_contract_date TEXT,
    commodity_summary_ai TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE commodities IS 'Commodities data synchronized from AirTable';


-- Table: Price Lists (AirTable ID: tbl0B7ON9dDTtj3mP)
CREATE TABLE IF NOT EXISTS price_lists (
    -- Primary key and AirTable reference
    id SERIAL PRIMARY KEY,
    airtable_record_id VARCHAR(20) UNIQUE,
    
    -- Data fields
    price_name TEXT,
    price_type VARCHAR(100),
    price_value DECIMAL(15,2),
    effective_date DATE,
    notes TEXT,
    commodity_name_lookup TEXT,
    contract_number_lookup TEXT,
    is_current_price INTEGER,
    days_since_effective INTEGER,
    related_contracts_rollup TEXT,
    price_summary_ai TEXT,
    market_price_research_ai TEXT,
    fieldspct5bpct5d TEXT,
    
    -- Metadata fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'pending',
    last_airtable_modified TIMESTAMP WITH TIME ZONE
);

COMMENT ON TABLE price_lists IS 'Price Lists data synchronized from AirTable';


-- Adding Foreign Key Constraints
-- These are added separately to avoid circular dependencies


-- Junction Tables for Many-to-Many Relationships
-- These tables handle the relationships between entities


CREATE TABLE IF NOT EXISTS contracts_hp_ng_customer (
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng_id, customers_id)
);

COMMENT ON TABLE contracts_hp_ng_customer IS 'Junction table for Contracts (Hợp Đồng).Customer relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng_commodity_type (
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng_id, commodities_id)
);

COMMENT ON TABLE contracts_hp_ng_commodity_type IS 'Junction table for Contracts (Hợp Đồng).Commodity Type relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng_related_shipments (
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng_id, shipments_id)
);

COMMENT ON TABLE contracts_hp_ng_related_shipments IS 'Junction table for Contracts (Hợp Đồng).Related Shipments relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng_related_inventory_movements (
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng_id, inventory_movements_id)
);

COMMENT ON TABLE contracts_hp_ng_related_inventory_movements IS 'Junction table for Contracts (Hợp Đồng).Related Inventory Movements relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng_price_lists (
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    price_lists_id INTEGER NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng_id, price_lists_id)
);

COMMENT ON TABLE contracts_hp_ng_price_lists IS 'Junction table for Contracts (Hợp Đồng).Price Lists relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng___2_customer (
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng___2_id, customers_id)
);

COMMENT ON TABLE contracts_hp_ng___2_customer IS 'Junction table for Contracts (Hợp Đồng) - 2.Customer relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng___2_commodity_type (
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng___2_id, commodities_id)
);

COMMENT ON TABLE contracts_hp_ng___2_commodity_type IS 'Junction table for Contracts (Hợp Đồng) - 2.Commodity Type relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng___2_related_shipments (
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng___2_id, shipments_id)
);

COMMENT ON TABLE contracts_hp_ng___2_related_shipments IS 'Junction table for Contracts (Hợp Đồng) - 2.Related Shipments relationship';


CREATE TABLE IF NOT EXISTS contracts_hp_ng___2_related_inventory_movements (
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contracts_hp_ng___2_id, inventory_movements_id)
);

COMMENT ON TABLE contracts_hp_ng___2_related_inventory_movements IS 'Junction table for Contracts (Hợp Đồng) - 2.Related Inventory Movements relationship';


CREATE TABLE IF NOT EXISTS customers_contracts (
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customers_id, contracts_hp_ng_id)
);

COMMENT ON TABLE customers_contracts IS 'Junction table for Customers.Contracts relationship';


CREATE TABLE IF NOT EXISTS customers_shipments (
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customers_id, shipments_id)
);

COMMENT ON TABLE customers_shipments IS 'Junction table for Customers.Shipments relationship';


CREATE TABLE IF NOT EXISTS customers_inventory_movements (
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customers_id, inventory_movements_id)
);

COMMENT ON TABLE customers_inventory_movements IS 'Junction table for Customers.Inventory Movements relationship';


CREATE TABLE IF NOT EXISTS customers_finished_goods (
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    finished_goods_id INTEGER NOT NULL REFERENCES finished_goods(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customers_id, finished_goods_id)
);

COMMENT ON TABLE customers_finished_goods IS 'Junction table for Customers.Finished Goods relationship';


CREATE TABLE IF NOT EXISTS customers_contracts_hp_ng___2 (
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (customers_id, contracts_hp_ng___2_id)
);

COMMENT ON TABLE customers_contracts_hp_ng___2 IS 'Junction table for Customers.Contracts (Hợp Đồng) - 2 relationship';


CREATE TABLE IF NOT EXISTS shipments_customer (
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipments_id, customers_id)
);

COMMENT ON TABLE shipments_customer IS 'Junction table for Shipments.Customer relationship';


CREATE TABLE IF NOT EXISTS shipments_contract_number (
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipments_id, contracts_hp_ng_id)
);

COMMENT ON TABLE shipments_contract_number IS 'Junction table for Shipments.Contract Number relationship';


CREATE TABLE IF NOT EXISTS shipments_commodity_type (
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipments_id, commodities_id)
);

COMMENT ON TABLE shipments_commodity_type IS 'Junction table for Shipments.Commodity Type relationship';


CREATE TABLE IF NOT EXISTS shipments_inventory_movements (
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipments_id, inventory_movements_id)
);

COMMENT ON TABLE shipments_inventory_movements IS 'Junction table for Shipments.Inventory Movements relationship';


CREATE TABLE IF NOT EXISTS shipments_contracts_hp_ng___2 (
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (shipments_id, contracts_hp_ng___2_id)
);

COMMENT ON TABLE shipments_contracts_hp_ng___2 IS 'Junction table for Shipments.Contracts (Hợp Đồng) - 2 relationship';


CREATE TABLE IF NOT EXISTS inventory_movements_customer (
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inventory_movements_id, customers_id)
);

COMMENT ON TABLE inventory_movements_customer IS 'Junction table for Inventory Movements.Customer relationship';


CREATE TABLE IF NOT EXISTS inventory_movements_commodity_type (
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inventory_movements_id, commodities_id)
);

COMMENT ON TABLE inventory_movements_commodity_type IS 'Junction table for Inventory Movements.Commodity Type relationship';


CREATE TABLE IF NOT EXISTS inventory_movements_related_contract (
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inventory_movements_id, contracts_hp_ng_id)
);

COMMENT ON TABLE inventory_movements_related_contract IS 'Junction table for Inventory Movements.Related Contract relationship';


CREATE TABLE IF NOT EXISTS inventory_movements_related_shipment (
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inventory_movements_id, shipments_id)
);

COMMENT ON TABLE inventory_movements_related_shipment IS 'Junction table for Inventory Movements.Related Shipment relationship';


CREATE TABLE IF NOT EXISTS inventory_movements_contracts_hp_ng___2 (
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (inventory_movements_id, contracts_hp_ng___2_id)
);

COMMENT ON TABLE inventory_movements_contracts_hp_ng___2 IS 'Junction table for Inventory Movements.Contracts (Hợp Đồng) - 2 relationship';


CREATE TABLE IF NOT EXISTS finished_goods_khch_hng (
    finished_goods_id INTEGER NOT NULL REFERENCES finished_goods(id) ON DELETE CASCADE,
    customers_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (finished_goods_id, customers_id)
);

COMMENT ON TABLE finished_goods_khch_hng IS 'Junction table for Finished Goods.Khách hàng relationship';


CREATE TABLE IF NOT EXISTS finished_goods_commodities (
    finished_goods_id INTEGER NOT NULL REFERENCES finished_goods(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (finished_goods_id, commodities_id)
);

COMMENT ON TABLE finished_goods_commodities IS 'Junction table for Finished Goods.Commodities relationship';


CREATE TABLE IF NOT EXISTS commodities_contracts (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, contracts_hp_ng_id)
);

COMMENT ON TABLE commodities_contracts IS 'Junction table for Commodities.Contracts relationship';


CREATE TABLE IF NOT EXISTS commodities_shipments (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    shipments_id INTEGER NOT NULL REFERENCES shipments(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, shipments_id)
);

COMMENT ON TABLE commodities_shipments IS 'Junction table for Commodities.Shipments relationship';


CREATE TABLE IF NOT EXISTS commodities_inventory_movements (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    inventory_movements_id INTEGER NOT NULL REFERENCES inventory_movements(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, inventory_movements_id)
);

COMMENT ON TABLE commodities_inventory_movements IS 'Junction table for Commodities.Inventory Movements relationship';


CREATE TABLE IF NOT EXISTS commodities_finished_goods (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    finished_goods_id INTEGER NOT NULL REFERENCES finished_goods(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, finished_goods_id)
);

COMMENT ON TABLE commodities_finished_goods IS 'Junction table for Commodities.Finished Goods relationship';


CREATE TABLE IF NOT EXISTS commodities_price_lists (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    price_lists_id INTEGER NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, price_lists_id)
);

COMMENT ON TABLE commodities_price_lists IS 'Junction table for Commodities.Price Lists relationship';


CREATE TABLE IF NOT EXISTS commodities_contracts_hp_ng___2 (
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    contracts_hp_ng___2_id INTEGER NOT NULL REFERENCES contracts_hp_ng___2(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (commodities_id, contracts_hp_ng___2_id)
);

COMMENT ON TABLE commodities_contracts_hp_ng___2 IS 'Junction table for Commodities.Contracts (Hợp Đồng) - 2 relationship';


CREATE TABLE IF NOT EXISTS price_lists_commodity (
    price_lists_id INTEGER NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    commodities_id INTEGER NOT NULL REFERENCES commodities(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (price_lists_id, commodities_id)
);

COMMENT ON TABLE price_lists_commodity IS 'Junction table for Price Lists.Commodity relationship';


CREATE TABLE IF NOT EXISTS price_lists_contract (
    price_lists_id INTEGER NOT NULL REFERENCES price_lists(id) ON DELETE CASCADE,
    contracts_hp_ng_id INTEGER NOT NULL REFERENCES contracts_hp_ng(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (price_lists_id, contracts_hp_ng_id)
);

COMMENT ON TABLE price_lists_contract IS 'Junction table for Price Lists.Contract relationship';


-- Indexes for Query Performance
-- These indexes optimize common query patterns

CREATE INDEX idx_contracts_hp_ng_airtable_id ON contracts_hp_ng(airtable_record_id);
CREATE INDEX idx_contracts_hp_ng_updated ON contracts_hp_ng(updated_at);

CREATE INDEX idx_contracts_hp_ng___2_airtable_id ON contracts_hp_ng___2(airtable_record_id);
CREATE INDEX idx_contracts_hp_ng___2_updated ON contracts_hp_ng___2(updated_at);

CREATE INDEX idx_customers_airtable_id ON customers(airtable_record_id);
CREATE INDEX idx_customers_updated ON customers(updated_at);

CREATE INDEX idx_shipments_airtable_id ON shipments(airtable_record_id);
CREATE INDEX idx_shipments_updated ON shipments(updated_at);

CREATE INDEX idx_inventory_movements_airtable_id ON inventory_movements(airtable_record_id);
CREATE INDEX idx_inventory_movements_updated ON inventory_movements(updated_at);

CREATE INDEX idx_finished_goods_airtable_id ON finished_goods(airtable_record_id);
CREATE INDEX idx_finished_goods_updated ON finished_goods(updated_at);

CREATE INDEX idx_commodities_airtable_id ON commodities(airtable_record_id);
CREATE INDEX idx_commodities_updated ON commodities(updated_at);

CREATE INDEX idx_price_lists_airtable_id ON price_lists(airtable_record_id);
CREATE INDEX idx_price_lists_updated ON price_lists(updated_at);



-- Utility Views for Data Management

CREATE OR REPLACE VIEW v_sync_status AS
SELECT 
    'contracts' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM contracts_hp_ng
UNION ALL
SELECT 
    'contracts_hp_ng___2' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM contracts_hp_ng___2
UNION ALL
SELECT 
    'customers' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM customers
UNION ALL
SELECT 
    'shipments' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM shipments
UNION ALL
SELECT 
    'inventory_movements' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM inventory_movements
UNION ALL
SELECT 
    'finished_goods' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM finished_goods
UNION ALL
SELECT 
    'commodities' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM commodities
UNION ALL
SELECT 
    'price_lists' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN sync_status = 'synced' THEN 1 END) as synced_records,
    COUNT(CASE WHEN sync_status = 'pending' THEN 1 END) as pending_records,
    MAX(updated_at) as last_update
FROM price_lists
;

COMMENT ON VIEW v_sync_status IS 'Overview of data synchronization status across all tables';
