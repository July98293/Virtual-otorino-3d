import numpy as np
import trimesh
from collections import defaultdict

def find_boundary_loops(mesh):
    edges_unique = mesh.edges_unique
    edges_inverse = mesh.edges_unique_inverse
    counts = np.bincount(edges_inverse)
    boundary_edges = edges_unique[counts==1]
    adj = defaultdict(list)
    for a,b in boundary_edges:
        adj[a].append(b)
        adj[b].append(a)
    visited = set()
    loops=[]
    for start in adj:
        if start in visited: continue
        loop=[start]; visited.add(start)
        prev=None; current=start
        while True:
            nxt=None
            for n in adj[current]:
                if n!=prev: nxt=n; break
            if nxt is None or nxt==start: break
            loop.append(nxt)
            visited.add(nxt)
            prev,current=current,nxt
        loops.append(loop)
    return loops

def close_all_holes(mesh):
    loops = find_boundary_loops(mesh)
    if not loops: return mesh
    V=mesh.vertices.copy()
    F=mesh.faces.copy()
    for loop in loops:
        pts = V[loop]
        centroid = pts.mean(axis=0)
        c_idx = len(V)
        V = np.vstack([V, centroid])
        for i in range(len(loop)):
            v0=loop[i]; v1=loop[(i+1)%len(loop)]
            F=np.vstack([F,[v0,v1,c_idx]])
    return trimesh.Trimesh(vertices=V, faces=F, process=True)
