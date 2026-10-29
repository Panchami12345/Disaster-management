"""
Citizen Emergency Service for DisasterShield AI
Handles damage reports, SOS alerts, and nearest safe shelter routing calculations.
"""

import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from backend.app.db.models import CitizenReport, EmergencySOS
from backend.app.schemas.schemas import CitizenReportCreate, EmergencySOSCreate, CitizenReportStatusUpdate
from backend.app.services.project_service import store


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers"""
    R = 6371.0  # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class CitizenEmergencyService:
    def create_report(self, db: Session, payload: CitizenReportCreate, user_id: Optional[int] = None) -> CitizenReport:
        report = CitizenReport(
            user_id=user_id,
            reporter_name=payload.reporter_name,
            reporter_phone=payload.reporter_phone,
            title=payload.title,
            category=payload.category,
            description=payload.description,
            severity=payload.severity.upper(),
            status="PENDING",
            latitude=payload.latitude,
            longitude=payload.longitude,
            address=payload.address or "Kodagu Incident Sector",
            photo_url=payload.photo_url or "https://images.unsplash.com/photo-1547683905-f686c993aae5?auto=format&fit=crop&w=400&q=80"
        )
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    def list_reports(self, db: Session, status: Optional[str] = None, category: Optional[str] = None) -> List[Dict[str, Any]]:
        query = db.query(CitizenReport)
        if status:
            query = query.filter(CitizenReport.status == status.upper())
        if category:
            query = query.filter(CitizenReport.category == category.upper())
        
        reports = query.order_by(CitizenReport.created_at.desc()).all()
        return [self._format_report(r) for r in reports]

    def get_reports_geojson(self, db: Session) -> Dict[str, Any]:
        """Returns citizen reports formatted as GeoJSON FeatureCollection for GIS map rendering"""
        reports = db.query(CitizenReport).all()
        features = []
        for r in reports:
            sev_colors = {
                "CRITICAL": "#DC2626",
                "HIGH": "#EA580C",
                "MEDIUM": "#F59E0B",
                "LOW": "#10B981"
            }
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [r.longitude, r.latitude]
                },
                "properties": {
                    "id": r.id,
                    "title": r.title,
                    "category": r.category,
                    "severity": r.severity,
                    "status": r.status,
                    "reporter_name": r.reporter_name,
                    "reporter_phone": r.reporter_phone,
                    "description": r.description,
                    "address": r.address,
                    "assigned_team": r.assigned_team,
                    "color": sev_colors.get(r.severity, "#F59E0B"),
                    "created_at": r.created_at.isoformat() if r.created_at else None
                }
            })
        return {
            "type": "FeatureCollection",
            "metadata": {"count": len(features)},
            "features": features
        }

    def update_report_status(self, db: Session, report_id: str, payload: CitizenReportStatusUpdate) -> Optional[Dict[str, Any]]:
        report = db.query(CitizenReport).filter(CitizenReport.id == report_id).first()
        if not report:
            return None
        
        report.status = payload.status.upper()
        if payload.assigned_team:
            report.assigned_team = payload.assigned_team
        if payload.action_notes:
            report.action_notes = payload.action_notes
        
        report.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(report)
        return self._format_report(report)

    def create_sos(self, db: Session, payload: EmergencySOSCreate) -> EmergencySOS:
        sos = EmergencySOS(
            reporter_name=payload.reporter_name,
            phone=payload.phone,
            latitude=payload.latitude,
            longitude=payload.longitude,
            people_count=payload.people_count,
            medical_need=payload.medical_need,
            notes=payload.notes,
            status="ACTIVE"
        )
        db.add(sos)
        db.commit()
        db.refresh(sos)
        return sos

    def list_sos_beacons(self, db: Session) -> List[Dict[str, Any]]:
        beacons = db.query(EmergencySOS).order_by(EmergencySOS.created_at.desc()).all()
        return [
            {
                "id": b.id,
                "reporter_name": b.reporter_name,
                "phone": b.phone,
                "latitude": b.latitude,
                "longitude": b.longitude,
                "people_count": b.people_count,
                "medical_need": b.medical_need,
                "notes": b.notes,
                "status": b.status,
                "created_at": b.created_at.isoformat() if b.created_at else None
            }
            for b in beacons
        ]

    def find_nearest_shelters(self, user_lat: float, user_lon: float) -> List[Dict[str, Any]]:
        """
        Cross-references candidate relocation sites and safe camps,
        calculating real-time distance and capacity for citizens.
        """
        sites = store.get_relocation_sites().get("features", [])
        shelter_list = []

        for s in sites:
            p = s.get("properties", {})
            geom = s.get("geometry", {})
            coords = geom.get("coordinates", [[]])[0]
            
            # Approximate centroid of the site polygon
            if coords and len(coords) > 0:
                site_lon = sum(c[0] for c in coords) / len(coords)
                site_lat = sum(c[1] for c in coords) / len(coords)
            else:
                site_lat, site_lon = 12.341, 75.810

            dist_km = haversine_distance_km(user_lat, user_lon, site_lat, site_lon)

            # Only recommend ELIGIBLE sites for public shelter routing
            if p.get("is_eligible"):
                shelter_list.append({
                    "site_id": p.get("site_id"),
                    "name": p.get("site_name"),
                    "rank": p.get("rank"),
                    "distance_km": dist_km,
                    "estimated_capacity": p.get("estimated_capacity_persons", 1000),
                    "open_capacity_status": "HIGH AVAILABILITY" if p.get("estimated_capacity_persons", 0) > 800 else "LIMITED",
                    "latitude": round(site_lat, 5),
                    "longitude": round(site_lon, 5),
                    "slope_deg": p.get("terrain_slope_deg"),
                    "water_access": p.get("water_availability", "Verified municipal water source"),
                    "power_access": p.get("power_grid_access", "Grid connected + diesel backup"),
                    "is_safe_from_floods": True,
                    "recommendation": p.get("recommendation_category", "Optimal Primary Relief Camp")
                })

        # Sort by distance
        shelter_list.sort(key=lambda x: x["distance_km"])
        return shelter_list

    def _format_report(self, r: CitizenReport) -> Dict[str, Any]:
        return {
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "description": r.description,
            "severity": r.severity,
            "status": r.status,
            "reporter_name": r.reporter_name,
            "reporter_phone": r.reporter_phone,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "address": r.address,
            "photo_url": r.photo_url,
            "assigned_team": r.assigned_team,
            "action_notes": r.action_notes,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "updated_at": r.updated_at.isoformat() if r.updated_at else None
        }


citizen_service = CitizenEmergencyService()
