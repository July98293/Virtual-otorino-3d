from fastapi import FastAPI, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import os, uuid, json
import numpy as np
import trimesh

from istimo import close_all_holes
from database import init_db, insert_ear_case


# --------------------
# Paths
# --------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "data", "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "outputs")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


# --------------------
# App
# --------------------
app = FastAPI(title="Istimo Brush ROI Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

init_db()


# --------------------
# Utils
# --------------------
def normalize_and_fix_mesh(
    mesh: trimesh.Trimesh,
    assume_input_unit="mm"
) -> trimesh.Trimesh:
    """
    Fix normali, chiude buchi, normalizza scala in mm
    e rende la mesh affidabile per il volume.
    """

    # --- pulizia base
    # mesh.remove_duplicate_faces()
    # mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()
    mesh.merge_vertices()

    # --- normali
    mesh.rezero()
    mesh.fix_normals()
    mesh.remove_infinite_values()

    # --- chiusura
    if not mesh.is_watertight:
        mesh = close_all_holes(mesh)

    # --- scala → mm
    scale_map = {
        "m": 1000.0,
        "cm": 10.0,
        "mm": 1.0
    }

    scale_factor = scale_map[assume_input_unit]
    mesh.apply_scale(scale_factor)

    return mesh


# --------------------
# Routes
# --------------------
@app.get("/")
def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.post("/upload_preview")
async def upload_preview(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(INPUT_DIR, f"{job_id}.stl")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    mesh = trimesh.load(input_path, force="mesh")

    return {
        "job_id": job_id,
        "vertices": mesh.vertices.tolist(),
        "faces": mesh.faces.tolist(),
        "watertight": bool(mesh.is_watertight),
        "faces_count": int(len(mesh.faces)),
        "vertices_count": int(len(mesh.vertices))
    }


@app.post("/process_brush")
async def process_brush(
    job_id: str = Form(...),
    verts: str = Form(...),
    faces: str = Form(...)
):
    verts = np.array(json.loads(verts))
    faces = np.array(json.loads(faces))

    mesh = trimesh.Trimesh(
        vertices=verts,
        faces=faces,
        process=False
    )

    # 🔑 FIX COMPLETO
    fixed = normalize_and_fix_mesh(
        mesh,
        assume_input_unit="mm"   # ← cambia se sai che arrivano in m
    )

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")
    fixed.export(output_path, file_type="ply", encoding="ascii")

    return {
        "job_id": job_id,
        "watertight": bool(fixed.is_watertight),
        "volume": float(fixed.volume),
        "faces": int(len(fixed.faces)),
        "vertices": int(len(fixed.vertices)),
        "download_url": f"/download/{job_id}"
    }


@app.get("/download/{job_id}")
def download(job_id: str):
    path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")
    return FileResponse(path, filename=f"{job_id}_closed.ply")


# --------------------
# SAVE CASE
# --------------------
@app.post("/save_case")
def save_case(payload: dict = Body(...)):
    case_id = str(uuid.uuid4())

    insert_ear_case(
        case_id=case_id,
        is_left=payload["is_left"],
        is_right=payload["is_right"],
        original_model_url=payload["original_model_url"],
        generated_model_url=payload["generated_model_url"],
        roi_vertices=payload["roi_vertices"],
        roi_faces=payload["roi_faces"],
        volume_mm3=payload["volume_mm3"],   # 🔑 coerente
        watertight=payload["watertight"],
        is_pathological=payload["is_pathological"],
        is_non_pathological=payload["is_non_pathological"],
        is_other=payload["is_other"],
        other_text=payload.get("other_text")
    )

    return {"status": "ok", "case_id": case_id}
