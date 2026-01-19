import os
import psycopg
from datetime import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set. Did you create a .env file?")
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id TEXT PRIMARY KEY,
                scan_filename TEXT,
                scan_data BYTEA,

                x_min REAL,
                x_max REAL,
                y_min REAL,
                y_max REAL,
                z_min REAL,
                z_max REAL,

                volume_mm3 REAL,

                classification TEXT,
                other_text TEXT,
                comment TEXT,

                created_at TIMESTAMP DEFAULT NOW()
            )
            """)
        conn.commit()


def insert_case(
    case_id,
    scan_filename,
    scan_bytes,
    x_min, x_max, y_min, y_max, z_min, z_max,
    volume_mm3,
    classification,
    other_text,
    comment
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO cases (
                id, scan_filename, scan_data,
                x_min, x_max, y_min, y_max, z_min, z_max,
                volume_mm3,
                classification, other_text, comment
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                case_id,
                scan_filename,
                scan_bytes,
                x_min, x_max,
                y_min, y_max,
                z_min, z_max,
                volume_mm3,
                classification,
                other_text,
                comment
            ))
        conn.commit()


def get_all_cases():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, scan_filename, volume_mm3, classification, created_at FROM cases")
            rows = cur.fetchall()
    return rows
