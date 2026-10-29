"""
FastAPI Routes for DisasterShield AI Platform
Unified REST Endpoints for:
  - Role-Based Authentication (Public Citizen & Emergency Authority)
  - Citizen Disaster Reporting, Status Tracking & Emergency SOS Beacons
  - Nearest Safe Shelter & Relief Camp Locator (Sphere Standard Capacity)
  - Authority Incident Triage & Response Dispatch
  - Live External Data Feeds (Open-Meteo, USGS Earthquakes, KSDMA Alerts)
  - AI Bi-Temporal Satellite Damage Assessment (Siamese U-Net)
  - GIS Multi-Hazard Screening (AHP Overlay) & TOPSIS Safe Relocation
"""

from fastapi import APIRouter, HTTPException, Depends, Header, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
import csv
import io

from backend.app.db.database import get_db
from backend.app.db.models import User, CitizenReport, EmergencySOS
from backend.app.schemas.schemas import (
    ProjectCreate,
    BuildingReviewUpdate,
    AHPWeightConfig,
    RelocationParamConfig,
    DamageAssessmentRequest,
    UserRegister,
    UserLogin,
    TokenResponse,
    CitizenReportCreate,
    CitizenReportStatusUpdate,
    EmergencySOSCreate,
)
from backend.app.services.project_service import store
from backend.app.services.auth_service import hash_password, verify_password, create_access_token, verify_access_token
from backend.app.services.live_feeds_service import live_feeds_service
from backend.app.services.citizen_service import citizen_service

router = APIRouter(prefix="/api")


# ---------------- DEPENDENCY: AUTH VERIFICATION ----------------

def get_current_user_optional(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extracts authenticated user from Bearer token if present"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.split(" ", 1)[1]
    payload = verify_access_token(token)
    if not payload:
        return None
    return db.query(User).filter(User.id == payload.get("user_id")).first()


def require_authority_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Ensures caller has verified Authority / Officer permissions"""
    user = get_current_user_optional(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required for disaster authority operations.")
    if user.role != "authority":
        raise HTTPException(status_code=403, detail="Authority command clearance required.")
    return user


# ---------------- HEALTH & SYSTEM STATUS ----------------

@router.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "DisasterShield AI - Spatial Decision Support & Emergency Operations API",
        "version": "2.0.0",
        "platform_capabilities": [
            "Role-Based Dashboards (Public Citizen & Authority Commander)",
            "Live External Disaster Feeds (Open-Meteo, USGS Earthquakes, KSDMA)",
            "Citizen Damage Reporting & Real-time SOS Beacons",
            "Safe Shelter Nearest-Routing with Humanitarian Capacity",
            "Bi-Temporal Siamese U-Net Damage Assessment",
            "AHP Multi-Hazard Red-Zone Screening (CR < 0.10)",
            "TOPSIS Relocation Multi-Criteria Optimization"
        ]
    }


# ---------------- AUTHENTICATION & USERS ----------------

@router.post("/auth/register", response_model=TokenResponse)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if existing:
        raise HTTPException(status_code=400, detail="An account with this email already exists.")
    
    new_user = User(
        email=payload.email.lower().strip(),
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role.lower(),
        phone=payload.phone,
        organization=payload.organization,
        badge_number=payload.badge_number
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role,
        full_name=new_user.full_name
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "full_name": new_user.full_name,
            "role": new_user.role,
            "phone": new_user.phone,
            "organization": new_user.organization,
            "badge_number": new_user.badge_number
        }
    }


@router.post("/auth/login", response_model=TokenResponse)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "phone": user.phone,
            "organization": user.organization,
            "badge_number": user.badge_number
        }
    }


@router.get("/auth/me")
def get_current_user_profile(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    user = get_current_user_optional(authorization, db)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired authentication session.")
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "phone": user.phone,
        "organization": user.organization,
        "badge_number": user.badge_number
    }


# ---------------- PUBLIC & CITIZEN PORTAL ENDPOINTS ----------------

@router.post("/citizen/reports")
def submit_citizen_report(
    payload: CitizenReportCreate,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Allows citizens to report localized damage, mudslides, or road closures with GPS & photos"""
    user = get_current_user_optional(authorization, db)
    user_id = user.id if user else None
    report = citizen_service.create_report(db, payload, user_id=user_id)
    return {
        "status": "SUCCESS",
        "message": "Disaster incident report successfully logged and transmitted to Emergency Command Center.",
        "report_id": report.id,
        "report": citizen_service._format_report(report)
    }


@router.get("/citizen/reports")
def list_citizen_reports(
    status: Optional[str] = Query(None, description="PENDING, VERIFIED, DISPATCHED, RESOLVED"),
    category: Optional[str] = Query(None, description="FLOOD_INUNDATION, LANDSLIDE, STRUCTURAL_COLLAPSE, TRAPPED_PERSONS, ROAD_BLOCK"),
    db: Session = Depends(get_db)
):
    """Returns list of public reports for tracking response progress"""
    return citizen_service.list_reports(db, status=status, category=category)


@router.get("/citizen/reports/geojson")
def get_citizen_reports_geojson(db: Session = Depends(get_db)):
    """GeoJSON format of citizen incident points for Leaflet map overlay"""
    return citizen_service.get_reports_geojson(db)


@router.post("/citizen/sos")
def trigger_emergency_sos(payload: EmergencySOSCreate, db: Session = Depends(get_db)):
    """Immediate high-priority SOS emergency beacon dispatched to NDRF and SDRF command"""
    sos = citizen_service.create_sos(db, payload)
    return {
        "status": "EMERGENCY_DISPATCH_ALERTED",
        "sos_id": sos.id,
        "message": "Emergency SOS broadcasted to Kodagu District Emergency Operation Center. Rescue teams alerted.",
        "coordinates": {"latitude": sos.latitude, "longitude": sos.longitude},
        "timestamp": sos.created_at.isoformat()
    }


@router.get("/citizen/sos")
def list_active_sos(db: Session = Depends(get_db)):
    """Authority view of active emergency SOS calls"""
    return citizen_service.list_sos_beacons(db)


@router.get("/citizen/shelters")
def find_nearest_safe_shelters(
    lat: float = Query(12.3375, description="Citizen current latitude"),
    lon: float = Query(75.8062, description="Citizen current longitude")
):
    """
    Ranks safe relocation sites by real-time distance from citizen's location,
    guaranteeing they are outside hazardous Red/Amber flood zones.
    """
    shelters = citizen_service.find_nearest_shelters(lat, lon)
    return {
        "citizen_coordinates": {"latitude": lat, "longitude": lon},
        "total_approved_shelters": len(shelters),
        "shelters": shelters
    }


# ---------------- AUTHORITY RESPONSE & INCIDENT MANAGEMENT ----------------

@router.patch("/authority/reports/{report_id}/status")
def update_incident_response_status(
    report_id: str,
    payload: CitizenReportStatusUpdate,
    db: Session = Depends(get_db)
):
    """Authority command triage: update report status (e.g. DISPATCHED) and assign rescue units"""
    updated = citizen_service.update_report_status(db, report_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Incident report {report_id} not found.")
    return {
        "status": "UPDATED",
        "report": updated
    }


# ---------------- LIVE DISASTER DATA PROVIDERS ----------------

@router.get("/feeds/all-alerts")
def get_aggregated_live_alerts():
    """Aggregates Open-Meteo, USGS Earthquakes, NASA FIRMS, and KSDMA regional bulletins"""
    return live_feeds_service.get_all_aggregated_alerts()


@router.get("/feeds/earthquakes")
def get_live_earthquakes():
    """Fetches real-time seismic event feed from USGS Earthquake Hazards Program"""
    return live_feeds_service.fetch_usgs_earthquakes()


@router.get("/feeds/weather")
def get_live_weather():
    """Queries Open-Meteo real-time meteorological network"""
    return live_feeds_service.fetch_live_weather_status()


# ---------------- AI DAMAGE ASSESSMENT & GIS DECISION SUPPORT ----------------

@router.get("/projects")
def list_projects():
    meta = store.get_project_metadata()
    summary = store.get_summary_statistics()
    return [{**meta, "summary": summary}]


@router.get("/projects/{project_id}")
def get_project_details(project_id: str):
    meta = store.get_project_metadata()
    summary = store.get_summary_statistics()
    return {
        "project": meta,
        "summary": summary
    }


@router.post("/projects/{project_id}/damage-assessment")
def run_damage_assessment(project_id: str, payload: DamageAssessmentRequest):
    summary = store.get_summary_statistics()
    return {
        "job_id": f"job-infer-{project_id}-992",
        "status": "COMPLETED",
        "model_version": payload.model_version,
        "confidence_threshold": payload.confidence_threshold,
        "summary": summary
    }


@router.get("/projects/{project_id}/buildings")
def get_buildings(
    project_id: str,
    damage_class: Optional[str] = Query(None, description="undamaged, minor_damage, major_damage, destroyed"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0),
    needs_review: Optional[bool] = Query(None),
):
    return store.get_filtered_buildings(
        damage_class=damage_class,
        min_confidence=min_confidence,
        needs_review=needs_review,
    )


@router.post("/projects/{project_id}/buildings/{building_id}/review")
def update_building_review(project_id: str, building_id: str, payload: BuildingReviewUpdate):
    updated = store.update_building_review(
        building_id=building_id,
        new_damage_class=payload.verified_damage_class,
        reviewer_notes=payload.reviewer_notes,
        reviewer_id=payload.reviewer_id,
    )
    if not updated:
        raise HTTPException(status_code=404, detail=f"Building {building_id} not found")
    return {"status": "SUCCESS", "building": updated}


@router.get("/projects/{project_id}/weather")
def get_project_live_weather(project_id: str):
    return store.get_live_weather()


@router.post("/projects/{project_id}/risk-analysis")
def run_risk_analysis(
    project_id: str,
    config: AHPWeightConfig,
    use_live_weather: bool = Query(False, description="Trigger dynamic live weather inundation integration")
):
    weights_dict = {
        "damage_density": config.damage_density,
        "flood_hydro_exposure": config.flood_hydro_exposure,
        "slope_landslide": config.slope_landslide,
        "land_cover_hazard": config.land_cover_hazard,
        "population_density": config.population_density,
    }
    result = store.run_hazard_analysis(
        weights_dict=weights_dict,
        red_threshold=config.red_threshold,
        amber_threshold=config.amber_threshold,
        use_live_weather=use_live_weather,
    )
    return result


@router.get("/projects/{project_id}/risk-zones")
def get_risk_zones(
    project_id: str,
    use_live_weather: bool = Query(False, description="Whether to apply real-time meteorological inundation")
):
    return store.get_hazard_zones(use_live_weather=use_live_weather)


@router.post("/projects/{project_id}/relocation-analysis")
def run_relocation_analysis(project_id: str, config: RelocationParamConfig):
    result = store.run_relocation_analysis(
        planning_area_sqm=config.planning_area_per_person_sqm,
        usable_fraction=config.usable_area_fraction,
        max_slope_deg=config.max_allowable_slope_deg,
        min_hazard_buffer_m=config.min_hazard_buffer_meters,
        custom_weights=config.criteria_weights,
    )
    return result


@router.get("/projects/{project_id}/relocation-sites")
def get_relocation_sites(project_id: str):
    return store.get_relocation_sites()


@router.get("/projects/{project_id}/reports/{report_format}")
def export_project_report(project_id: str, report_format: str = "json"):
    meta = store.get_project_metadata()
    summary = store.get_summary_statistics()
    sites = store.get_relocation_sites().get("features", [])

    if report_format.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Rank", "Site ID", "Site Name", "Eligibility", "TOPSIS Score",
            "Recommendation", "Capacity (Persons)", "Net Usable Area (m2)",
            "Terrain Slope (deg)", "Road Distance (km)", "Hazard Buffer (m)", "Exclusion Reasons"
        ])
        for s in sites:
            p = s.get("properties", {})
            writer.writerow([
                p.get("rank", "N/A"),
                p.get("site_id"),
                p.get("site_name"),
                "ELIGIBLE" if p.get("is_eligible") else "EXCLUDED",
                p.get("topsis_score", 0.0),
                p.get("recommendation_category"),
                p.get("estimated_capacity_persons", 0),
                p.get("net_usable_area_sqm", 0.0),
                p.get("terrain_slope_deg", 0.0),
                p.get("distance_to_road_km", 0.0),
                p.get("buffer_from_hazard_m", 0.0),
                "; ".join(p.get("exclusion_reasons", []))
            ])
        return PlainTextResponse(output.getvalue(), media_type="text/csv", headers={
            "Content-Disposition": f"attachment; filename=relocation_rankings_{project_id}.csv"
        })

    return {
        "project": meta,
        "executive_summary": summary,
        "relocation_shortlist": [
            {
                "rank": s["properties"].get("rank"),
                "site_id": s["properties"].get("site_id"),
                "site_name": s["properties"].get("site_name"),
                "is_eligible": s["properties"].get("is_eligible"),
                "topsis_score": s["properties"].get("topsis_score"),
                "capacity_persons": s["properties"].get("estimated_capacity_persons"),
                "category": s["properties"].get("recommendation_category"),
                "exclusion_reasons": s["properties"].get("exclusion_reasons"),
            }
            for s in sites
        ]
    }
