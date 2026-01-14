# Otorino 3D  

This repository contains the core geometric engine behind **Otorino 3D**.  
It is a FastAPI-based backend designed to transform raw anatomical meshes into
clean, analyzable, and manufacturable biological surfaces.

The system is built to operate directly on 3D anatomy (STL / PLY meshes),
treating the human body as a geometric object that can be *measured, sliced,
repaired, and quantified*.

---

## What the Code Does

The pipeline implemented here performs five fundamental operations:

1. **Upload & Preview**
   - Accepts an anatomical mesh (e.g. from CT reconstruction or 3D scanning)
   - Loads it with `trimesh`
   - Returns vertices and faces for real-time visualization
   - Reports mesh integrity (watertightness, face count, vertex count)

2. **Region of Interest (ROI) Extraction**
   - The user defines a 3D bounding box:
     ```
     x_min, x_max  
     y_min, y_max  
     z_min, z_max
     ```
   - The system extracts only the anatomical region inside that volume  
   - This allows isolating specific structures:
     - ear canal segments  
     - cartilage regions  
     - bone compartments  
     - pathological zones  

3. **Topological Analysis**
   - Boundary edges are detected by analyzing edge multiplicity
   - Open manifolds are reconstructed as ordered boundary loops
   - This treats anatomy as a *mathematical surface*, not just a mesh

4. **Procedural Hole Closing**
   - Each open boundary is closed by:
     - computing its centroid  
     - generating new triangular faces  
     - synthesizing a continuous surface  
   - The result is a **watertight biological solid**

5. **Quantitative Output**
   - The processed mesh is:
     - exported as PLY  
     - validated for watertightness  
     - measured for:
       - volume  
       - face count  
       - vertex count  

##what cam we do

Instead of describing degeneration, compression, or growth qualitatively,
we can now compute:

- bone volume  
- cavity volume  
- structural loss  
- morphological asymmetry  

directly from real anatomy.

---

## Architecture

- `FastAPI` – API layer  
- `trimesh` – mesh processing  
- `numpy` – geometric computation  
- Custom algorithms for:
  - ROI extraction  
  - boundary loop detection  
  - anatomical hole closure  

Endpoints:

- `POST /upload_preview`  
  Upload mesh and return preview data

- `POST /process`  
  Extract ROI, close anatomy, compute metrics

- `GET /download/{job_id}`  
  Download the processed mesh
