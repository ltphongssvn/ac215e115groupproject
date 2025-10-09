# Technical Documentation - Rice Market Data Pipeline

## Architecture Overview

The Rice Market Data Pipeline synchronizes data between AirTable (flexible, user-friendly database) and PostgreSQL (strict, performant relational database). This synchronization handles the impedance mismatch between these two systems through sophisticated transformation and validation layers.

## Key Technical Challenges and Solutions

### 1. Vietnamese Character Handling

**Challenge**: Field names like "BX Á Châu" (Asia warehouse) contain Vietnamese diacritics that aren't valid in SQL identifiers.

**Solution**: Our sanitization function strips non-ASCII characters and replaces them with underscores. However, this created inconsistencies between how the DDL generator and sync script handled the same names.

**Implementation**: The `_sanitize_column_name()` method in `UltimateAirTableClient` handles this transformation consistently.

### 2. SQL Identifier Compliance

**Challenge**: Some AirTable field names like "Đêm 16h30-19h" (Night shift 4:30-7PM) become "16h30_19h" after sanitization, which is invalid SQL because it starts with a number.

**Solution**: We detect when sanitized names would start with a digit and prefix them with 'n_' (from "Đêm"/night) to maintain SQL compliance while preserving semantic meaning.

### 3. Column Name Mapping Discrepancies

**Challenge**: The DDL generation and synchronization processes applied slightly different transformations, creating mismatches like:
- `bx_a_chin` (sync) vs `bx_a__chin` (database)
- `s_lng_theo_u_bao_trong_gi` (sync) vs `s_lng_theo_u_bao___trong_gi` (database)

**Solution**: We maintain explicit mappings in `CompleteProductionSync.column_mappings` dictionary, discovered through iterative debugging.

### 4. Data Validation Issues

**Challenge**: Percentage fields sometimes contained impossible values like 9,472,482.51% (likely formulas or accumulated totals).

**Solution**: The `ValidatingAirTableClient` detects values over 100 in percentage fields and either divides by 100 (if likely stored as whole numbers) or caps at 99.999 (for DECIMAL(5,3) fields).

## Data Model

The system synchronizes 8 tables representing rice market operations:

| Table | Records | Purpose |
|-------|---------|---------|
| customers | 105 | Business relationships |
| commodities | 45 | Rice varieties and products |
| price_lists | 5 | Pricing structures |
| contracts_hp_ng | 1,968 | Purchase agreements (part 1) |
| contracts_hp_ng___2 | 1,280 | Purchase agreements (part 2) |
| shipments | 383 | Delivery tracking |
| inventory_movements | 8,342 | Warehouse flow (BX locations) |
| finished_goods | 1,690 | Production output by shift |

## Synchronization Modes

### Full Sync
- Fetches all records from AirTable
- Replaces all data in PostgreSQL
- Used for initial setup or recovery

### Incremental Sync
- Only fetches records modified since last sync
- Uses `last_airtable_modified` timestamp
- Much faster for regular updates

## Performance Characteristics

- **Throughput**: ~150-200 records/second
- **API Rate**: 100 records per AirTable API call
- **Network Overhead**: ~0.3-0.4 seconds per API call
- **Database Write**: Bulk upsert for efficiency

## Error Recovery

The system handles several error categories:

1. **Network Errors**: Automatic retry with exponential backoff
2. **Data Validation Errors**: Log warning and apply safe defaults
3. **Schema Mismatches**: Use explicit column mappings
4. **API Rate Limits**: Respect AirTable's rate limiting

## Monitoring

Check synchronization health:
```bash
python monitor.py
```

View latest sync report:
```bash
cat logs/sync_report_final.txt
```

Watch real-time logs:
```bash
tail -f logs/sync.log
```

## Future Improvements

1. **Parallel Processing**: Synchronize multiple tables concurrently
2. **Change Detection**: Only update actually modified fields
3. **Conflict Resolution**: Handle concurrent modifications
4. **Schema Evolution**: Automatic detection of new AirTable fields
5. **Data Archival**: Move old inventory movements to archive tables
