"""
SQLAlchemy ORM models for DisasterShield AI
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.db.database import Base


def get_utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="citizen", nullable=False)  # 'citizen' or 'authority'
    phone = Column(String(20), nullable=True)
    organization = Column(String(100), nullable=True)  # e.g. "KSDMA Kodagu Division"
    badge_number = Column(String(50), nullable=True)  # for emergency personnel
    created_at = Column(DateTime, default=get_utc_now)

    reports = relationship("CitizenReport", back_populates="user")


class CitizenReport(Base):
    __tablename__ = "citizen_reports"

    id = Column(String(50), primary_key=True, default=lambda: f"REP-{uuid.uuid4().hex[:8].upper()}")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reporter_name = Column(String(100), nullable=False)
    reporter_phone = Column(String(20), nullable=False)
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # 'FLOOD_INUNDATION', 'LANDSLIDE', 'STRUCTURAL_COLLAPSE', 'TRAPPED_PERSONS', 'ROAD_BLOCK'
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    status = Column(String(20), default="PENDING")  # 'PENDING', 'VERIFIED', 'DISPATCHED', 'RESOLVED'
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(255), nullable=True)
    photo_url = Column(String(500), nullable=True)
    assigned_team = Column(String(100), nullable=True)
    action_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=get_utc_now)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now)

    user = relationship("User", back_populates="reports")


class EmergencySOS(Base):
    __tablename__ = "emergency_sos"

    id = Column(String(50), primary_key=True, default=lambda: f"SOS-{uuid.uuid4().hex[:6].upper()}")
    reporter_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    people_count = Column(Integer, default=1)
    medical_need = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)
    status = Column(String(20), default="ACTIVE")  # 'ACTIVE', 'DISPATCHED', 'RESOLVED'
    created_at = Column(DateTime, default=get_utc_now)


class DisasterAlert(Base):
    __tablename__ = "disaster_alerts"

    id = Column(String(50), primary_key=True, default=lambda: f"ALT-{uuid.uuid4().hex[:6].upper()}")
    source = Column(String(100), nullable=False)  # 'IMD Warning', 'USGS Seismic', 'Open-Meteo', 'KSDMA'
    title = Column(String(200), nullable=False)
    severity = Column(String(20), default="WARNING")  # 'INFO', 'WARNING', 'CRITICAL'
    affected_region = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    coordinates_lat = Column(Float, nullable=True)
    coordinates_lon = Column(Float, nullable=True)
    issued_at = Column(DateTime, default=get_utc_now)
    is_active = Column(Boolean, default=True)
