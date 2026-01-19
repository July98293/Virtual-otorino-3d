from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, FileResponse
import trimesh
import uuid
import os
from istimo import extract_roi, close_all_holes
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
load_dotenv()
from database import init_db
init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "data", "inputs")
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "outputs")
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="Istimo Mesh Processor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/frontend", StaticFiles(directory=FRONTEND_DIR), name="frontend")

@app.get("/")
def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

# ----------------------------
# Upload & preview
# ----------------------------
@app.post("/upload_preview")
async def upload_preview(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(INPUT_DIR, f"{job_id}.stl")

    with open(input_path, "wb") as f:
        f.write(await file.read())

    mesh = trimesh.load(input_path, force="mesh")
    vertices = mesh.vertices.tolist()
    faces = mesh.faces.tolist()

    return {
        "job_id": job_id,
        "vertices": vertices,
        "faces": faces,
        "watertight": mesh.is_watertight,
        "faces_count": len(mesh.faces),
        "vertices_count": len(mesh.vertices)
    }

# ----------------------------
# Process ROI and close
# ----------------------------
@app.post("/process")
async def process_mesh(
    job_id: str = Form(...),
    x_min: float = Form(...),
    x_max: float = Form(...),
    y_min: float = Form(...),
    y_max: float = Form(...),
    z_min: float = Form(...),
    z_max: float = Form(...)
):
    input_path = os.path.join(INPUT_DIR, f"{job_id}.stl")
    output_path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")

    mesh = trimesh.load(input_path, force="mesh")
    sub = extract_roi(mesh, x_min, x_max, y_min, y_max, z_min, z_max)
    closed = close_all_holes(sub)
    closed.export(output_path, file_type="ply", encoding="ascii")

    return {
        "job_id": job_id,
        "watertight": bool(closed.is_watertight),
        "volume": float(closed.volume),
        "faces": int(len(closed.faces)),
        "vertices": int(len(closed.vertices)),
        "download_url": f"/download/{job_id}"
    }

# ----------------------------
# Download
# ----------------------------
@app.get("/download/{job_id}")
def download_mesh(job_id: str):
    path = os.path.join(OUTPUT_DIR, f"{job_id}_closed.ply")
    return FileResponse(path, media_type="application/octet-stream", filename=f"{job_id}_closed.ply")
