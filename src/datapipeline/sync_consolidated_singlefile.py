#!/usr/bin/env python3
# /home/lenovo/code/ltphongssvn/ac215e115groupproject/data-pipeline/sync_consolidated_singlefile.py
#
# Single-file, self-contained Airtable → PostgreSQL synchronization script.
# Includes:
#   - Config loader (from .env or environment)
#   - Airtable client with pagination + incremental sync (IS_AFTER(LAST_MODIFIED_TIME(), ...))
#   - Column-name sanitization matching your DDL (remove non-ASCII, pct, underscores)
#   - Guard to avoid leading-digit identifiers (prefix n_/f_ as needed)
#   - Per-table explicit column mappings you validated in production
#   - Uses Airtable TABLE IDs (prevents 403 Forbidden on some tables)
#   - Coerces Airtable {"specialValue":"NaN"} placeholders to SQL NULL on ingest
#   - PostgreSQL connection pool + ON CONFLICT (airtable_record_id) upsert
#   - Orchestrator running the 8 canonical tables discovered in your DB
#   - Post-sync verification: per-table counts + grand total

import os
import sys
import time
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Tuple, Any, Optional

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass

import requests
import psycopg2
from psycopg2.pool import SimpleConnectionPool


# ---------- Logging ----------
logger = logging.getLogger("airtable_sync_onefile")
logger.setLevel(logging.INFO)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(_handler)


# ---------- Config ----------
class SyncConfig:
    def __init__(self, d: Dict[str, Any]):
        self.airtable_api_key: str = d.get("AIRTABLE_API_KEY", "")
        self.airtable_base_id: str = d.get("AIRTABLE_BASE_ID", "")
        self.airtable_api_url: str = "https://api.airtable.com/v0"

        self.postgres_host: str = d.get("POSTGRES_HOST", "localhost")
        self.postgres_port: int = int(d.get("POSTGRES_PORT", 5433))
        self.postgres_database: str = d.get("POSTGRES_DATABASE", "rice_market_db")
        self.postgres_user: str = d.get("POSTGRES_USER", "rice_admin")
        self.postgres_password: str = d.get("POSTGRES_PASSWORD", "")
        self.postgres_schema: str = d.get("POSTGRES_SCHEMA", "airtable_sync")

        self.sync_mode: str = d.get("SYNC_MODE", "incremental").lower()
        self.rate_limit_delay: float = float(d.get("RATE_LIMIT_DELAY", 0.25))  # seconds

    @classmethod
    def from_env(cls) -> "SyncConfig":
        return cls(dict(os.environ))


# ---------- Airtable Client (sanitization + pagination + incremental) ----------
class AirtableClient:
    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
        tok = (cfg.airtable_api_key or "").strip()
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {tok}"})
        # Table ID mapping copied from your working client
        self.table_ids: Dict[str, str] = {
            'contracts_hp_ng': 'tbl7sHbwOCOTjL2MC',
            'contracts_hp_ng___2': 'tbllz4cazITSwnXIo',
            'customers': 'tblDUfIlNy07Z0hiL',
            'shipments': 'tblSj7JcxYYfs6Dcl',
            'inventory_movements': 'tblhb3Vxhi6Yt0BDw',
            'finished_goods': 'tblNY26FnHswHRcWS',
            'commodities': 'tblawXefYSXa6UFSX',
            'price_lists': 'tbl0B7ON9dDTtj3mP'
        }

    def _sanitize_column_name(self, name: str) -> str:
        safe = name.lower()
        for ch in [' ', '-', '/', '.', '(', ')', '[', ']']:
            safe = safe.replace(ch, '_')
        safe = safe.replace('%', 'pct')
        # remove non-ASCII
        safe = ''.join(c for c in safe if ord(c) < 128)
        # keep only alnum or underscore
        safe = ''.join(c if (c.isalnum() or c == '_') else '' for c in safe)
        while '__' in safe:
            safe = safe.replace('__', '_')
        safe = safe.strip('_') or 'field'
        # guard: leading digit not allowed in identifiers
        if safe[0].isdigit():
            if 'h' in safe and any(c.isdigit() for c in safe):
                safe = 'n_' + safe
            else:
                safe = 'f_' + safe
        return safe

    @staticmethod
    def _normalize_percent_value(val: Any) -> Optional[float]:
        """
        Convert Airtable percent-ish values to a DECIMAL(5,3)-safe float:
        - Accepts numbers or strings like '85', '85%', '0.85', '12,3 %'
        - If abs(value) > 1, assume whole percent -> divide by 100
        - Cap to [-99.999, 99.999] (fits NUMERIC(5,3))
        """
        if val is None:
            return None
        try:
            if isinstance(val, str):
                s = val.strip().replace(',', '')
                if s.endswith('%'):
                    s = s[:-1].strip()
                num = float(s)
            elif isinstance(val, (int, float)):
                num = float(val)
            else:
                return None

            if abs(num) > 1:
                num = num / 100.0

            if num > 99.999:
                num = 99.999
            if num < -99.999:
                num = -99.999
            return num
        except Exception:
            return None

    def _apply_pct_normalization(self, out: Dict[str, Any]) -> None:
        """
        Normalize *all* columns whose sanitized name includes 'pct'.
        This covers e.g.: fat_pct, moisture_pct, loss_1_3pct_from_1_6_2025, acid_value_pct, etc.
        """
        for key in list(out.keys()):
            if 'pct' in key and out[key] is not None:
                norm = self._normalize_percent_value(out[key])
                if norm is not None:
                    out[key] = norm

    @staticmethod
    def _is_special_json_nan_obj(v: Any) -> bool:
        """True if v is a dict like {'specialValue': 'NaN'} (case-sensitive match)."""
        return isinstance(v, dict) and v.get('specialValue') == 'NaN'

    @staticmethod
    def _is_special_json_nan_str(s: str) -> bool:
        """
        True if s decodes to {'specialValue':'NaN'} or literally contains that structure.
        Handles both exact JSON and variants with whitespace.
        """
        if not isinstance(s, str):
            return False
        # Fast path literal containment
        if '{"specialValue": "NaN"}' in s or '{"specialValue":"NaN"}' in s:
            return True
        # Try to parse
        try:
            obj = json.loads(s)
            return isinstance(obj, dict) and obj.get('specialValue') == 'NaN'
        except Exception:
            return False

    def _transform_record(self, rec: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """
        Transform Airtable record:
        - Convert Airtable {"specialValue":"NaN"} to Python None (→ SQL NULL)
        - Skip link fields (lists of 'rec...' IDs) to avoid writing non-existent columns
        - JSON-encode dicts and all non-link lists to avoid psycopg2 adaptation errors
        - Normalize any '*pct' fields to NUMERIC(5,3)-safe values
        """
        fields = rec.get("fields", {})
        out: Dict[str, Any] = {}

        def _encode(v: Any) -> Any:
            # Treat Airtable special-value NaN as NULL
            if AirtableClient._is_special_json_nan_obj(v):
                return None
            if isinstance(v, str) and AirtableClient._is_special_json_nan_str(v):
                return None

            # Link field: list of Airtable record IDs -> skip entirely
            if isinstance(v, list) and v and all(isinstance(x, str) and x.startswith("rec") for x in v):
                return "__SKIP_LINK_FIELD__"

            # Complex types -> JSON string
            if isinstance(v, (dict, list)):
                return json.dumps(v, ensure_ascii=False)

            # Scalar or None is fine
            return v

        for k, v in fields.items():
            col = self._sanitize_column_name(k)
            val = _encode(v)
            if val == "__SKIP_LINK_FIELD__":  # skip link arrays
                continue
            out[col] = val

        # Normalize percent-like fields
        self._apply_pct_normalization(out)

        out["airtable_record_id"] = rec.get("id")
        out["last_airtable_modified"] = rec.get("createdTime")
        return out

    def fetch_table_records(self, table_name: str, last_sync: Optional[datetime]) -> List[Dict[str, Any]]:
        # Use the Airtable TABLE ID, not the name (fixes 403)
        table_id = self.table_ids.get(table_name)
        if not table_id:
            raise ValueError(f"Unknown table: {table_name}")
        url = f"{self.cfg.airtable_api_url}/{self.cfg.airtable_base_id}/{table_id}"

        params: Dict[str, Any] = {"pageSize": 100}
        if self.cfg.sync_mode == "incremental" and last_sync:
            # IS_AFTER(LAST_MODIFIED_TIME(), '...ISO...')
            iso = last_sync.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            params["filterByFormula"] = f"IS_AFTER(LAST_MODIFIED_TIME(), '{iso}')"

        all_recs: List[Dict[str, Any]] = []
        offset = None
        while True:
            if offset:
                params["offset"] = offset
            r = self.session.get(url, params=params, timeout=30)
            if r.status_code == 429:
                time.sleep(1.2)
                continue
            r.raise_for_status()
            data = r.json()
            for rec in data.get("records", []):
                all_recs.append(self._transform_record(rec, table_name))
            offset = data.get("offset")
            if not offset:
                break
            time.sleep(self.cfg.rate_limit_delay)
        logger.info(f"Completed fetching {len(all_recs)} total records from {table_name}")
        return all_recs


# ---------- PostgreSQL Sync ----------
class PostgreSQLSync:
    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
        self.pool = SimpleConnectionPool(
            1, 10,
            host=cfg.postgres_host,
            port=cfg.postgres_port,
            database=cfg.postgres_database,
            user=cfg.postgres_user,
            password=cfg.postgres_password,
        )
        # Explicit mappings consolidated from your latest code
        self.column_mappings: Dict[str, Dict[str, str]] = {
            'contracts_hp_ng': {
                'total_price_incl_transport': 'total_price_incl__transport'
            },
            'contracts_hp_ng___2': {
                'total_price_with_vc': 'total_price_with_vc',
                'imported_quantity_n': 'imported_quantity_n'
            },
            'inventory_movements': {
                'bx_a_chin': 'bx_a__chin',
                'bx_a_dng': 'bx_a_dng',
                'bx_ngoi_ni': 'bx_ngoi_ni',
                'bx_ti': 'bx_ti',
                'bx_tr': 'bx_tr',
                'bx_thoa': 'bx___thoa',
                'loss_13pct_from_1_6_2025': 'loss_1_3pct_from_1_6_2025',
                'ldh_kh': 'ldh_kh',
            },
            'finished_goods': {
                's_lng_theo_u_bao_trong_gi': 's_lng_theo_u_bao___trong_gi',
                's_lng_theo_u_bao_ngoi_gi': 's_lng_theo_u_bao___ngoi_gi',
                's_lng_theo_u_bao_trong_gi_ca_2': 's_lng_theo_u_bao___trong_gi_ca_2',
                's_lng_theo_u_bao_ngoi_gi_ca_2': 's_lng_theo_u_bao___ngoi_gi_ca_2',
                'n_16h30_19h': 'n_16h30_19h',
                'n_19h_7h': 'n_19h_7h',
                'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_1': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_1',
                'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_2': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_2',
                'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_3': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_3',
                'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_4': 'ngoi_gi_87k_19_7h_l_cn_ca_m_ca_4',
                'ngoi_gi_75k_ch_nht_ca_1': 'ngoi_gi_75k__ch_nht_ca_1',
                'ngoi_gi_75k_ch_nht_ca_4': 'ngoi_gi_75k__ch_nht_ca_4',
                'trong_gi_57k_ca_4': 'trong_gi_57k_ca_4',
            },
        }

    def _conn(self):
        return self.pool.getconn()

    def _put(self, conn):
        self.pool.putconn(conn)

    def get_last_sync_time(self, table_name: str) -> Optional[datetime]:
        q = f"SELECT MAX(updated_at) FROM {self.cfg.postgres_schema}.{table_name}"
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(q)
                row = cur.fetchone()
                return row[0] if row and row[0] else None
        except Exception as e:
            logger.warning(f"Could not determine last sync time for {table_name}: {e}")
            return None
        finally:
            self._put(conn)

    def _map_columns(self, table: str, rec: Dict[str, Any]) -> Dict[str, Any]:
        mapping = self.column_mappings.get(table, {})
        return {mapping.get(k, k): v for k, v in rec.items()}

    def upsert_records(self, table_name: str, records: List[Dict[str, Any]]) -> Tuple[int, int]:
        if not records:
            return (0, 0)
        mapped = [self._map_columns(table_name, r) for r in records]
        inserted = updated = 0
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                for r in mapped:
                    cols = list(r.keys()) + ["sync_status", "updated_at"]
                    vals = list(r.values()) + ["synced", datetime.now(timezone.utc)]
                    placeholders = ", ".join(["%s"] * len(vals))
                    col_list = ", ".join(cols)
                    update_cols = [c for c in cols if c != "airtable_record_id"]
                    update_expr = ", ".join([f"{c}=EXCLUDED.{c}" for c in update_cols])
                    q = f"""
                        INSERT INTO {self.cfg.postgres_schema}.{table_name}
                        ({col_list})
                        VALUES ({placeholders})
                        ON CONFLICT (airtable_record_id)
                        DO UPDATE SET {update_expr}
                        RETURNING (xmax = 0) AS inserted
                    """
                    cur.execute(q, vals)
                    res = cur.fetchone()
                    if res and res[0]:
                        inserted += 1
                    else:
                        updated += 1
            conn.commit()
            logger.info(f"Upserted into {table_name}: inserted={inserted}, updated={updated}")
        except Exception as e:
            conn.rollback()
            logger.error(f"Upsert error in {table_name}: {e}")
            raise
        finally:
            self._put(conn)
        return inserted, updated


# ---------- Orchestrator ----------
class SyncOrchestrator:
    TABLES = [
        "customers",
        "commodities",
        "price_lists",
        "contracts_hp_ng",
        "contracts_hp_ng___2",
        "shipments",
        "inventory_movements",
        "finished_goods",
    ]

    def __init__(self, cfg: SyncConfig):
        self.cfg = cfg
        self.airtable = AirtableClient(cfg)
        self.pg = PostgreSQLSync(cfg)

    def sync_table(self, table_name: str) -> Dict[str, Any]:
        logger.info(f"Starting sync for table: {table_name}")
        last_sync: Optional[datetime] = None
        if self.cfg.sync_mode == "incremental":
            last_sync = self.pg.get_last_sync_time(table_name)
            if last_sync:
                logger.info(f"Performing incremental sync since {last_sync.isoformat()}")
        recs = self.airtable.fetch_table_records(table_name, last_sync)
        if not recs:
            return {"table": table_name, "status": "success", "records_processed": 0,
                    "inserted": 0, "updated": 0, "duration_seconds": 0.0}
        t0 = time.time()
        ins, upd = self.pg.upsert_records(table_name, recs)
        dt = time.time() - t0
        return {"table": table_name, "status": "success", "records_processed": len(recs),
                "inserted": ins, "updated": upd, "duration_seconds": dt}

    def sync_all_tables(self) -> List[Dict[str, Any]]:
        results = []
        for t in self.TABLES:
            try:
                res = self.sync_table(t)
            except Exception as e:
                logger.error(f"Failed syncing {t}: {e}")
                res = {"table": t, "status": "failed", "error": str(e), "records_processed": 0}
            results.append(res)
            time.sleep(self.cfg.rate_limit_delay)
        return results


# ---------- Verification ----------
def verify_counts(cfg: SyncConfig) -> Tuple[List[Tuple[str, int]], int]:
    dsn = dict(
        host=cfg.postgres_host,
        port=cfg.postgres_port,
        dbname=cfg.postgres_database,
        user=cfg.postgres_user,
        password=cfg.postgres_password,
    )
    per: List[Tuple[str, int]] = []
    total = 0
    with psycopg2.connect(**dsn) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema=%s AND table_type='BASE TABLE'
                        ORDER BY table_name
                        """, (cfg.postgres_schema,))
            tables = [r[0] for r in cur.fetchall()]
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM {cfg.postgres_schema}.{t}")
                c = int(cur.fetchone()[0])
                per.append((t, c))
                total += c
    return per, total


# ---------- Main ----------
def main() -> int:
    cfg = SyncConfig.from_env()
    if not cfg.airtable_api_key:
        print("ERROR: AIRTABLE_API_KEY not configured"); return 1
    if not cfg.airtable_base_id:
        print("ERROR: AIRTABLE_BASE_ID not configured"); return 1

    print("\n" + "="*74)
    print(" RICE MARKET — CONSOLIDATED ONE-FILE SYNC")
    print("="*74)
    print(f" Source: Airtable base {cfg.airtable_base_id}")
    print(f" Target: PostgreSQL {cfg.postgres_host}:{cfg.postgres_port} / DB {cfg.postgres_database}")
    print(f" Schema: {cfg.postgres_schema}")
    print(f" Mode:   {cfg.sync_mode.upper()}")
    print("="*74)

    orch = SyncOrchestrator(cfg)
    start = datetime.now()
    results = orch.sync_all_tables()

    succ = [r for r in results if r.get("status")=="success"]
    fail = [r for r in results if r.get("status")=="failed"]
    tot_proc = sum(r.get("records_processed", 0) for r in succ)
    tot_ins = sum(r.get("inserted", 0) for r in succ)
    tot_upd = sum(r.get("updated", 0) for r in succ)
    elapsed = (datetime.now() - start).total_seconds()

    print("\n--- Synchronization Summary -----------------------------------------")
    print(f" Tables attempted: {len(results)}")
    print(f" Success: {len(succ)} | Failed: {len(fail)}")
    if fail:
        for f in fail:
            print(f"   ✗ {f.get('table','?')}: {str(f.get('error','Unknown'))[:120]}")
    print(f" Records processed: {tot_proc:,} (inserted: {tot_ins:,}, updated: {tot_upd:,})")
    if elapsed > 0:
        print(f" Duration: {elapsed:.1f}s | Throughput: {int(tot_proc/elapsed) if tot_proc else 0} rec/s")

    print("\n--- Post-Sync Verification (DB counts) -------------------------------")
    try:
        per, total = verify_counts(cfg)
        for t, c in per:
            print(f"  - {t}: {c}")
        print(f"\nGrand total rows across schema '{cfg.postgres_schema}': {total}")
    except Exception as e:
        print(f"WARNING: verification failed: {e}")

    print("\nDone.")
    return 0 if not fail else 2


if __name__ == "__main__":
    sys.exit(main())
