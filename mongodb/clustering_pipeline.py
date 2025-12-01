import json
import os
import sys
import time
import numpy as np
from pathlib import Path
from collections import defaultdict

from sklearn.cluster import DBSCAN
import umap.umap_ as umap
from google.genai import types

project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from mongodb.handlers import get_all_complaints
from llm.llm_client import gemini_client
from llm.prompts import CLUSTER_SUMMARY_PROMPT

UMAP_NEIGHBORS = 15
UMAP_COMPONENTS = 5
UMAP_METRIC = 'cosine'
DBSCAN_EPS = 0.5
DBSCAN_MIN_SAMPLES = 3
TOP_DOCS_FOR_SUMMARY = 30
OUTPUT_FILE = "clusters.json"

def generate_cluster_summary(descriptions, retries=5):
    formatted_prompt = CLUSTER_SUMMARY_PROMPT.format(descriptions=descriptions)
    
    for attempt in range(retries):
        try:
            response = gemini_client.client.models.generate_content(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
                contents=formatted_prompt
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[WARNING] Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                wait_time = (2 ** (attempt + 1)) + np.random.uniform(0, 1)
                print(f"[WAIT] Retrying in {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            else:
                print(f"[ERROR] All {retries} attempts failed.")
                return {"cluster_name": "Unknown", "cluster_summary": "Error generating summary after multiple retries."}

def run_clustering_pipeline():
    print("[START] Starting Clustering Pipeline...")

    print("[INFO] Fetching complaints from MongoDB...")
    complaints = get_all_complaints({"embedding": {"$exists": True}})
    
    if not complaints:
        print("[ERROR] No complaints with embeddings found. Exiting.")
        return

    print(f"[SUCCESS] Fetched {len(complaints)} complaints.")

    embeddings = [c["embedding"] for c in complaints]
    ids = [str(c["_id"]) for c in complaints]
    descriptions = [c.get("description", "") for c in complaints]
    
    X = np.array(embeddings)
    
    print(f"[INFO] Reducing dimensions for {len(X)} documents using UMAP...")
    reducer = umap.UMAP(
        n_neighbors=UMAP_NEIGHBORS, 
        n_components=UMAP_COMPONENTS,
        metric=UMAP_METRIC,
        random_state=42
    )
    X_reduced = reducer.fit_transform(X)

    print("[INFO] Clustering data using DBSCAN...")
    clusterer = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES)
    labels = clusterer.fit_predict(X_reduced)

    clusters = defaultdict(list)
    for idx, label in enumerate(labels):
        clusters[label].append({
            "description": descriptions[idx],
            "vector": X_reduced[idx]
        })
    
    final_output = []
    print(f"[INFO] Found {len(clusters)} clusters (including noise). Processing summaries...")
    
    for label, items in clusters.items():
        if label == -1:
            print(f"   - Processing Uncategorized ({len(items)} items)")
            final_output.append({
                "cluster_id": -1,
                "cluster_name": "Uncategorized",
                "cluster_summary": "Miscellaneous complaints that do not fit into distinct clusters.",
                "count": len(items),
                "complaints": [item["description"] for item in items]
            })
            continue
            
        vectors = np.array([item["vector"] for item in items])
        centroid = np.mean(vectors, axis=0)
        
        distances = np.linalg.norm(vectors - centroid, axis=1)
        top_indices = np.argsort(distances)[:TOP_DOCS_FOR_SUMMARY]
        top_descriptions = [items[i]["description"] for i in top_indices]
        
        print(f"   - Summarizing Cluster {label} ({len(items)} items)...")
        
        summary_data = generate_cluster_summary("\n- ".join(top_descriptions))
        
        final_output.append({
            "cluster_id": int(label),
            "cluster_name": summary_data.get("cluster_name", f"Cluster {label}"),
            "cluster_summary": summary_data.get("cluster_summary", "No summary available."),
            "count": len(items),
            "complaints": [item["description"] for item in items]
        })
        
        time.sleep(2)
        
    final_output.sort(key=lambda x: x['cluster_id'] if x['cluster_id'] != -1 else float('inf'))

    output_path = Path(__file__).parent / OUTPUT_FILE
    with open(output_path, "w") as f:
        json.dump(final_output, f, indent=4)
        
    print(f"[SUCCESS] Clustering complete! Results saved to: {output_path}")
    return output_path



