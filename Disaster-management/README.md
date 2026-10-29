# DisasterShield AI
### AI-Powered Post-Disaster Damage Assessment, Live GIS Mapping & Relocation Decision Support System

An enterprise-grade, GIS-enabled spatial decision-support platform designed to transform disaster management from reactive response to proactive spatial planning. The system combines deep learning on bi-temporal satellite imagery, multi-hazard AHP risk screening, real-time meteorological and seismic alerts, citizen emergency reporting, and multi-criteria TOPSIS candidate relocation ranking across **dual role-based dashboards**.

---

## 🌟 Key Platform Capabilities

### 1. 🛡️ Authority Command Center
- **Tactical GIS Operations Map:** Live Leaflet-based map with high-resolution satellite imagery (Esri), OpenStreetMap, and Topographic views.
- **Incident Triage & Response Dispatch:** Monitor citizen disaster reports and emergency SOS beacons in real-time, dispatching first responder units (NDRF/SDRF) with audit tracking.
- **AHP Multi-Hazard Screening:** Mathematical weighted overlay across structural damage density, flood runoff, slope, land cover, and population exposure with live Consistency Ratio validation ($CR < 0.10$).
- **TOPSIS Safe Relocation Shortlist:** Automated screening enforcing mandatory exclusionary criteria (slope $\le 16^\circ$, safe buffer $\ge 250\text{ m}$) and ranking candidate plots by Sphere humanitarian capacity ($C = A \cdot u / a$).
- **Human-in-the-Loop Building Inspector:** Inspect softmax probability distributions and override AI classifications with a single click.

### 2. 👥 Public & Citizen Portal
- **One-Tap Emergency SOS Beacon:** Broadcasts live GPS coordinates, trapped headcounts, and medical alerts directly to District Emergency Operations.
- **Citizen Damage Reporting:** Submit geotagged field incident reports with photographic evidence, damage category, and severity assessment.
- **Nearest Safe Shelter Locator:** Automatically computes real-time distance (in km) to approved safe camps outside hazardous Red Zones, showing remaining capacity, verified water, and power backup.
- **Live Response Tracker:** Track submitted incident requests with visual progress updates (`PENDING` $\rightarrow$ `DISPATCHED` $\rightarrow$ `RESOLVED`).

### 3. 🔬 AI & GIS Assessment Workspace
- **Interactive Bi-Temporal Satellite Comparison:** Swipe slider comparing pre-disaster Sentinel-2 imagery against post-disaster PlanetScope high-resolution tiles.
- **4-Tier Damage Classification:** Shared-weight Siamese U-Net with feature-difference fusion classifying structures into *Undamaged*, *Minor Damage*, *Major Damage*, and *Destroyed*.
- **Uncertainty Gating:** Flags predictions with confidence $< 0.65$ for manual review.

### 4. 🌐 Real-Time External Data Integrations
- **Open-Meteo:** Live precipitation, temperature, humidity, wind, and 24h cumulative rainfall driving dynamic flood inundation models.
- **USGS Earthquake Hazards Program:** Real-time seismic event feed monitoring regional tremors ($M \ge 2.5$).
- **NASA FIRMS / Hotspots:** Active fire and thermal anomaly monitoring.
- **KSDMA & IMD Advisories:** Official regional disaster warning bulletins and evacuation alerts.

---

## 🚀 Quick Start Guide

### 1. Requirements
- Python 3.10+ (tested with Python 3.13 on Windows 11)
- Key Libraries: PyTorch, Rasterio, GeoPandas, Shapely, FastAPI, SQLAlchemy, Uvicorn

### 2. Run the Platform
Run the platform launcher:
```powershell
.\.venv\Scripts\python.exe run_platform.py
```
Or start Uvicorn directly:
```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000
```
Then navigate to:
- **DisasterShield AI Web Application:** `http://127.0.0.1:8000`
- **Interactive API Documentation:** `http://127.0.0.1:8000/docs`

### 3. Run Automated Tests
Execute the full test suite (18 passing tests covering GIS, ML models, API endpoints, Auth, Citizen Reports, and Live Feeds):
```powershell
.\.venv\Scripts\python.exe -m pytest gis/tests backend/tests ml/tests -v
```

---

## 👥 Demo Authentication Personas

The platform includes two pre-configured demo personas accessible via the header dropdown:
1. **Authority Commander:**
   - Email: `officer@sdma.gov.in`
   - Password: `admin123`
   - Clearance: KSDMA Incident Command Center
2. **Public Citizen:**
   - Email: `citizen@gmail.com`
   - Password: `citizen123`
   - Role: Kodagu District Resident

---

## 📚 Technical Documentation
- **[System Architecture](docs/ARCHITECTURE.md):** Modular 4-tier pipeline and database schema design.
- **[AHP & TOPSIS Methodology](docs/AHP_TOPSIS_METHODOLOGY.md):** Mathematical formulation, formulas, and proofs.
- **[Data Management Catalogue](docs/DATA_CATALOGUE.md):** Satellite data, DEM, and meteorological references.
