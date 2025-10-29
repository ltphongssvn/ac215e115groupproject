<!-- /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/README.md -->

# Data Pipeline — Airtable → PostgreSQL (Consolidated Sync)

This README documents the single-file sync script and the guardrails added to prevent Airtable JSON `{"specialValue":"NaN"}` leaking into numeric fields, plus percent normalization and verification steps.

---

## 1) Script

**Path:** `/home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/sync_consolidated_singlefile.py`

### Key behaviors
- Uses **Airtable Table IDs** (prevents 403 on some bases).
- **Sanitizes column names** to match DB identifiers.
- **Converts** Airtable `{"specialValue":"NaN"}` (object or string) **to SQL NULL** on ingest.
- **Normalizes percent-like fields**: any sanitized column containing `pct` is parsed to a **NUMERIC(5,3)-safe** float (e.g., `"85%"` → `0.85`).
- Skips link fields (arrays of `rec...`) and JSON-encodes remaining complex values.
- PostgreSQL upsert via `ON CONFLICT (airtable_record_id) DO UPDATE`.
- Incremental mode (`SYNC_MODE=incremental`) with `IS_AFTER(LAST_MODIFIED_TIME())`.

---

## 2) Configuration

Environment variables (read from shell or `.env` in this folder):

- `AIRTABLE_API_KEY` — Required (Airtable personal access token).
- `AIRTABLE_BASE_ID` — Required.
- `POSTGRES_HOST` (default `localhost`)
- `POSTGRES_PORT` (default `5433`)
- `POSTGRES_DATABASE` (default `rice_market_db`)
- `POSTGRES_USER` (default `rice_admin`)
- `POSTGRES_PASSWORD` (default `localdev123`)
- `POSTGRES_SCHEMA` (default `airtable_sync`)
- `SYNC_MODE` — `full` or `incremental` (default `incremental`)
- `RATE_LIMIT_DELAY` — seconds between page fetches (default `0.25`)

---

## 3) Running the sync

Examples:

```bash
# Full refresh
AIRTABLE_API_KEY=*** SYNC_MODE=full python data-pipeline/sync_consolidated_singlefile.py

# Incremental
AIRTABLE_API_KEY=*** SYNC_MODE=incremental python data-pipeline/sync_consolidated_singlefile.py
````

Expected output ends with a per-table count and grand total.

---

## 4) DB schema hardening (commodities)

We aligned two columns to real numerics and added non-negative checks:

```sql
-- Types
ALTER TABLE airtable_sync.commodities
  ALTER COLUMN average_unit_price_from_contracts TYPE NUMERIC(12,3)
    USING NULLIF(average_unit_price_from_contracts,'')::NUMERIC,
  ALTER COLUMN total_contracted_quantity_kg TYPE NUMERIC(18,3)
    USING NULLIF(total_contracted_quantity_kg,'')::NUMERIC;

-- Constraints
ALTER TABLE airtable_sync.commodities
  ADD CONSTRAINT commodities_avg_price_nonneg
    CHECK (average_unit_price_from_contracts IS NULL OR average_unit_price_from_contracts >= 0),
  ADD CONSTRAINT commodities_total_qty_nonneg
    CHECK (total_contracted_quantity_kg IS NULL OR total_contracted_quantity_kg >= 0);
```

These prevent accidental reintroduction of malformed or negative values.

---

## 5) Verification playbooks

### A. Global sentinel for JSON NaN

Create once, then call anytime:

```sql
-- Create
DROP FUNCTION IF EXISTS airtable_sync.find_json_nan();
CREATE FUNCTION airtable_sync.find_json_nan()
RETURNS TABLE (out_table_name text, out_column_name text, matches int)
LANGUAGE plpgsql AS $$
DECLARE r record; cnt int; sql text;
BEGIN
  FOR r IN
    SELECT c.table_name, c.column_name
    FROM information_schema.columns c
    WHERE c.table_schema='airtable_sync'
      AND c.data_type IN ('text','character varying')
    ORDER BY c.table_name, c.column_name
  LOOP
    sql := format('SELECT count(*) FROM %I.%I WHERE %I LIKE %L',
                  'airtable_sync', r.table_name, r.column_name,
                  '%{"specialValue": "NaN"}%');
    EXECUTE sql INTO cnt;
    IF cnt > 0 THEN
      out_table_name := r.table_name;
      out_column_name := r.column_name;
      matches := cnt;
      RETURN NEXT;
    END IF;
  END LOOP;
  RETURN;
END $$;

-- Use
SELECT * FROM airtable_sync.find_json_nan();
```

Expected: **0 rows**.

### B. Commodities numeric health

```sql
SELECT COUNT(*) FILTER (WHERE average_unit_price_from_contracts IS NOT NULL) AS nonnull_prices,
       MIN(average_unit_price_from_contracts) AS min_price,
       AVG(average_unit_price_from_contracts) AS avg_price,
       MAX(average_unit_price_from_contracts) AS max_price
FROM airtable_sync.commodities;

SELECT COUNT(*) FILTER (WHERE total_contracted_quantity_kg IS NOT NULL) AS nonnull_qty,
       SUM(total_contracted_quantity_kg) AS sum_qty,
       AVG(total_contracted_quantity_kg) AS avg_qty,
       MIN(total_contracted_quantity_kg) AS min_qty,
       MAX(total_contracted_quantity_kg) AS max_qty
FROM airtable_sync.commodities;
```

### C. Backsliding check (exact JSON text)

```sql
SELECT COUNT(*) AS json_nan_backsliding
FROM airtable_sync.commodities
WHERE average_unit_price_from_contracts::text LIKE '%{"specialValue": "NaN"}%'
   OR total_contracted_quantity_kg::text LIKE '%{"specialValue": "NaN"}%';
-- Expect 0
```

---

## 6) Why these changes

* Airtable can represent missing numerics as JSON `{ "specialValue": "NaN" }`.
* Storing those verbatim breaks SQL aggregations and downstream services (NL+SQL, RAG, forecasting).
* The sync now **coerces** those sentinels to **NULL** and ensures percent fields are numeric.
* DB constraints/type changes prevent accidental regressions.

---

## 7) Troubleshooting

* **401 Unauthorized**: confirm `AIRTABLE_API_KEY` and `AIRTABLE_BASE_ID`.
* **429 Too Many Requests**: increase `RATE_LIMIT_DELAY`.
* **numeric field overflow**: caused by bad percent inputs; fixed by `%` normalization. If seen elsewhere, open an issue with a sample record.

---

## 8) Operational checklist for releases

1. Run a **full sync** in staging.
2. Run `SELECT * FROM airtable_sync.find_json_nan();` → **0 rows**.
3. Run Commodities numeric health queries → values present, no negatives.
4. Promote to production.

