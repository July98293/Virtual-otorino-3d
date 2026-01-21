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

# CREATE TABLE ON STARTUP
init_db()

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
        "watertight": mesh.is_watertight,
        "faces_count": len(mesh.faces),
        "vertices_count": len(mesh.vertices)
    }


@app.post("/process_brush")
async def process_brush(
    job_id: str = Form(...),
    verts: str = Form(...),
    faces: str = Form(...)
):
    verts = np.array(json.loads(verts))
    faces = np.array(json.loads(faces))

    mesh = trimesh.Trimesh(vertices=verts, faces=faces, process=True)
    closed = close_all_holes(mesh)

    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")
    closed.export(output_path, file_type="ply", encoding="ascii")

    return {
        "job_id": job_id,
        "watertight": bool(closed.is_watertight),
        "volume": float(closed.volume),
        "faces": int(len(closed.faces)),
        "vertices": int(len(closed.vertices)),
        "download_url": f"/download/{job_id}"
    }


@app.get("/download/{job_id}")
def download(job_id: str):
    path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")
    return FileResponse(path, filename=f"{job_id}_closed.ply")


# --------------------
# SAVE CASE (FIXED)
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
        volume_mm3=payload["volume_mm3"],
        watertight=payload["watertight"],
        is_pathological=payload["is_pathological"],
        is_non_pathological=payload["is_non_pathological"],
        is_other=payload["is_other"],
        other_text=payload.get("other_text")
    )

    return {"status": "ok", "case_id": case_id}
