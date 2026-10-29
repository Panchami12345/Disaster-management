"""
Tests for DisasterShield AI new features:
Authentication, Citizen Reports, SOS Beacons, Shelter Finder, and Live Alerts.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_aggregated_live_alerts():
    res = client.get("/api/feeds/all-alerts")
    assert res.status_code == 200
    data = res.json()
    assert "alerts" in data
    assert "weather" in data
    assert len(data["alerts"]) > 0


def test_user_registration_and_login():
    # Test registration
    email = "test_user_77@example.com"
    reg_payload = {
        "email": email,
        "password": "securepassword123",
        "full_name": "Test Citizen",
        "role": "citizen",
        "phone": "+91-99999-11111"
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code in [200, 400]  # 400 if already created in previous run

    # Test login
    login_payload = {
        "email": email,
        "password": "securepassword123"
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    assert token_data["user"]["email"] == email


def test_citizen_report_submission_and_query():
    report_payload = {
        "reporter_name": "Kiran S.",
        "reporter_phone": "+91-98765-43210",
        "title": "Severe road submergence near culvert",
        "category": "FLOOD_INUNDATION",
        "description": "Culvert overflowed, road submerged under 2 feet of swift water.",
        "severity": "HIGH",
        "latitude": 12.3390,
        "longitude": 75.8050,
        "address": "Koppa West Junction"
    }
    res = client.post("/api/citizen/reports", json=report_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SUCCESS"
    assert "report_id" in data
    report_id = data["report_id"]

    # Verify query
    list_res = client.get("/api/citizen/reports")
    assert list_res.status_code == 200
    reports = list_res.json()
    assert any(r["id"] == report_id for r in reports)

    # Authority update status
    patch_res = client.patch(f"/api/authority/reports/{report_id}/status", json={
        "status": "DISPATCHED",
        "assigned_team": "Kodagu SDRF Unit 1",
        "action_notes": "Rescue vehicle dispatched."
    })
    assert patch_res.status_code == 200
    assert patch_res.json()["report"]["status"] == "DISPATCHED"


def test_emergency_sos_beacon():
    sos_payload = {
        "reporter_name": "Deepa K.",
        "phone": "+91-99887-66554",
        "latitude": 12.3360,
        "longitude": 75.8080,
        "people_count": 3,
        "medical_need": True,
        "notes": "Water surrounded ground floor."
    }
    res = client.post("/api/citizen/sos", json=sos_payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "EMERGENCY_DISPATCH_ALERTED"
    assert "sos_id" in data


def test_nearest_shelter_finder():
    res = client.get("/api/citizen/shelters?lat=12.3375&lon=75.8062")
    assert res.status_code == 200
    data = res.json()
    assert "shelters" in data
    assert len(data["shelters"]) > 0
    # First shelter should have positive capacity and distance
    first = data["shelters"][0]
    assert "distance_km" in first
    assert "estimated_capacity" in first
    assert first["distance_km"] >= 0.0
