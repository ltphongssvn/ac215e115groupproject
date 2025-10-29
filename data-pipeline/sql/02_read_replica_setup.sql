-- data-pipeline/scripts/02_read_replica_setup.sql
-- Read replica simulation setup for local development
-- This script creates read-only users and configurations that mirror Cloud SQL read replica behavior

-- Create a read-only role that simulates read replica access patterns
CREATE ROLE rice_readonly_role NOLOGIN;

-- Grant connection rights to the database
GRANT CONNECT ON DATABASE rice_market_db TO rice_readonly_role;

-- Grant usage on the airtable_sync schema
GRANT USAGE ON SCHEMA airtable_sync TO rice_readonly_role;
GRANT USAGE ON SCHEMA public TO rice_readonly_role;

-- Grant SELECT permissions on all existing tables in airtable_sync schema
GRANT SELECT ON ALL TABLES IN SCHEMA airtable_sync TO rice_readonly_role;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA airtable_sync TO rice_readonly_role;

-- Ensure future tables also get SELECT permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA airtable_sync 
    GRANT SELECT ON TABLES TO rice_readonly_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA airtable_sync 
    GRANT SELECT ON SEQUENCES TO rice_readonly_role;

-- Create read-only user for application connections
-- In production, this would be the user that connects to read replicas
CREATE USER rice_reader WITH PASSWORD 'readonly_pass_123';
GRANT rice_readonly_role TO rice_reader;

-- Create a monitoring user for health checks and metrics
-- This simulates Cloud SQL's monitoring capabilities
CREATE USER rice_monitor WITH PASSWORD 'monitor_pass_123';
GRANT CONNECT ON DATABASE rice_market_db TO rice_monitor;
GRANT USAGE ON SCHEMA airtable_sync TO rice_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA pg_catalog TO rice_monitor;
GRANT SELECT ON ALL TABLES IN SCHEMA information_schema TO rice_monitor;

-- Create a function to check replication lag (simulated for local dev)
-- In Cloud SQL, this would report actual replication lag to read replicas
CREATE OR REPLACE FUNCTION airtable_sync.get_replication_lag()
RETURNS TABLE (
    lag_seconds NUMERIC,
    last_sync TIMESTAMP WITH TIME ZONE,
    is_healthy BOOLEAN
) AS $$
BEGIN
    -- In local dev, we always return 0 lag
    -- In production, this would query pg_stat_replication
    RETURN QUERY
    SELECT 
        0::NUMERIC as lag_seconds,
        CURRENT_TIMESTAMP as last_sync,
        true as is_healthy;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create a view to monitor table sizes and row counts
-- This helps identify which tables need read replica optimization
CREATE OR REPLACE VIEW airtable_sync.v_table_stats AS
SELECT 
    schemaname,
    relname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) AS total_size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) AS table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname) - 
                   pg_relation_size(schemaname||'.'||relname)) AS indexes_size,
    n_live_tup AS approximate_row_count,
    n_dead_tup AS dead_rows,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'airtable_sync'
ORDER BY pg_total_relation_size(schemaname||'.'||relname) DESC;

-- Grant read access to the monitoring view
GRANT SELECT ON airtable_sync.v_table_stats TO rice_readonly_role;
GRANT SELECT ON airtable_sync.v_table_stats TO rice_monitor;

-- Create a connection pooling configuration table
-- This simulates how Cloud SQL manages connection pooling for read replicas
CREATE TABLE IF NOT EXISTS airtable_sync.connection_pool_config (
    pool_name VARCHAR(50) PRIMARY KEY,
    min_connections INTEGER DEFAULT 5,
    max_connections INTEGER DEFAULT 20,
    connection_timeout INTEGER DEFAULT 30,
    idle_timeout INTEGER DEFAULT 600,
    is_read_replica BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert default pooling configurations
INSERT INTO airtable_sync.connection_pool_config (pool_name, min_connections, max_connections, is_read_replica)
VALUES 
    ('primary_pool', 10, 50, false),
    ('read_replica_pool', 5, 30, true),
    ('analytics_pool', 2, 10, true)
ON CONFLICT (pool_name) DO NOTHING;

-- Create a query routing rules table
-- This demonstrates how queries would be routed to read replicas in production
CREATE TABLE IF NOT EXISTS airtable_sync.query_routing_rules (
    rule_id SERIAL PRIMARY KEY,
    table_pattern VARCHAR(255),
    query_type VARCHAR(50), -- SELECT, INSERT, UPDATE, DELETE
    route_to VARCHAR(50), -- primary, read_replica, cache
    priority INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Insert routing rules that demonstrate read replica patterns
INSERT INTO airtable_sync.query_routing_rules (table_pattern, query_type, route_to, priority)
VALUES 
    ('contracts%', 'SELECT', 'read_replica', 100),
    ('customers%', 'SELECT', 'read_replica', 100),
    ('inventory%', 'SELECT', 'read_replica', 90),
    ('commodities%', 'SELECT', 'cache', 110), -- Frequently accessed, rarely changed
    ('%', 'INSERT', 'primary', 100),
    ('%', 'UPDATE', 'primary', 100),
    ('%', 'DELETE', 'primary', 100)
ON CONFLICT DO NOTHING;

-- Create an audit log for read vs write query patterns
-- This helps optimize read replica usage in production
CREATE TABLE IF NOT EXISTS airtable_sync.query_audit_log (
    log_id SERIAL PRIMARY KEY,
    query_type VARCHAR(20),
    table_name VARCHAR(100),
    execution_time_ms INTEGER,
    rows_affected INTEGER,
    user_name VARCHAR(50),
    application_name VARCHAR(100),
    is_cached BOOLEAN DEFAULT false,
    executed_on VARCHAR(20), -- primary or read_replica
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index for efficient audit log queries
CREATE INDEX idx_query_audit_created ON airtable_sync.query_audit_log(created_at DESC);
CREATE INDEX idx_query_audit_type ON airtable_sync.query_audit_log(query_type, table_name);

-- Grant appropriate permissions
GRANT SELECT ON airtable_sync.connection_pool_config TO rice_readonly_role;
GRANT SELECT ON airtable_sync.query_routing_rules TO rice_readonly_role;
GRANT INSERT ON airtable_sync.query_audit_log TO rice_readonly_role;

-- Create a comment explaining the read replica simulation
COMMENT ON ROLE rice_readonly_role IS 'Read-only role simulating Cloud SQL read replica access patterns';
COMMENT ON ROLE rice_reader IS 'Application user for read-only queries (simulates read replica connections)';
COMMENT ON TABLE airtable_sync.query_routing_rules IS 'Demonstrates how queries are routed between primary and read replicas';

-- Output confirmation
DO $$
BEGIN
    RAISE NOTICE 'Read replica simulation setup complete';
    RAISE NOTICE 'Created read-only user: rice_reader';
    RAISE NOTICE 'Created monitoring user: rice_monitor';
    RAISE NOTICE 'Query routing rules configured for read replica patterns';
END $$;
