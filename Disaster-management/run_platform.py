"""
One-Click Platform Launcher for DisasterShield AI
Starts the FastAPI backend, initializes SQLite database, and launches the interactive Web Dashboard.
"""

import sys
import os
import time
import webbrowser

def main():
    print("=" * 70)
    print("  DISASTERSHIELD AI: ENTERPRISE DISASTER SPATIAL DECISION PLATFORM")
    print("  AI Damage Assessment • Live GIS Mapping • TOPSIS Relocation")
    print("=" * 70)

    # Add project root to sys.path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    print("\n[1/3] Verifying core AI & GIS runtime dependencies...")
    try:
        import torch
        import rasterio
        import geopandas
        import fastapi
        import uvicorn
        import sqlalchemy
        print("      [OK] PyTorch, Rasterio, GeoPandas, SQLAlchemy, and FastAPI are ready.")
    except ImportError as e:
        print(f"      [!] Missing requirement: {e}")
        sys.exit(1)

    print("\n[2/3] Checking dataset files & database initialization...")
    sample_meta = os.path.join(project_root, "data", "samples", "project_metadata.json")
    if not os.path.exists(sample_meta):
        print("      * Generating sample study dataset...")
        from data.samples.generate_sample_project import generate_sample_study_dataset
        generate_sample_study_dataset(os.path.join(project_root, "data", "samples"))
    
    # Initialize & seed SQLite database for DisasterShield AI
    from backend.app.db.seed_data import init_and_seed_db
    init_and_seed_db()
    print("      [OK] DisasterShield AI database and disaster study dataset are loaded.")

    url = "http://127.0.0.1:8000"
    print(f"\n[3/3] Starting DisasterShield AI Decision Server at: {url}")
    print(f"      * Authority Command Center & Citizen Portal: {url}")
    print(f"      * Swagger REST API Documentation: {url}/docs")
    print(f"      * Press Ctrl+C to terminate the server.\n")

    # Open browser automatically after a brief delay
    time.sleep(1.0)
    webbrowser.open(url)

    # Launch uvicorn
    import uvicorn
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)

if __name__ == "__main__":
    main()
