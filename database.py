import os
import psycopg
from datetime import datetime
from dotenv import load_dotenv
import json
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_conn():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not set. Did you create a .env file?")
    return psycopg.connect(DATABASE_URL)


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            DROP TABLE IF EXISTS ear_cases;
            """)
            cur.execute("""
            CREATE TABLE ear_cases (
                id TEXT PRIMARY KEY,

                is_left BOOLEAN NOT NULL,
                is_right BOOLEAN NOT NULL,

                original_model_url TEXT NOT NULL,
                generated_model_url TEXT NOT NULL,

                roi_vertices JSONB NOT NULL,
                roi_faces JSONB NOT NULL,

                volume_mm3 REAL,
                watertight BOOLEAN,

                is_pathological BOOLEAN NOT NULL,
                is_non_pathological BOOLEAN NOT NULL,
                is_other BOOLEAN NOT NULL,
                other_text TEXT,

                created_at TIMESTAMP DEFAULT NOW()
            );
            """)
        conn.commit()


def insert_ear_case(
    case_id,
    is_left,
    is_right,
    original_model_url,
    generated_model_url,
    roi_vertices,
    roi_faces,
    volume_mm3,
    watertight,
    is_pathological,
    is_non_pathological,
    is_other,
    other_text
):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            INSERT INTO ear_cases (
                id,
                is_left,
                is_right,
                original_model_url,
                generated_model_url,
                roi_vertices,
                roi_faces,
                volume_mm3,
                watertight,
                is_pathological,
                is_non_pathological,
                is_other,
                other_text
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                case_id,
                is_left,
                is_right,
                original_model_url,
                generated_model_url,
                json.dumps(roi_vertices),
                json.dumps(roi_faces),
                volume_mm3,
                watertight,
                is_pathological,
                is_non_pathological,
                is_other,
                other_text
            ))
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
