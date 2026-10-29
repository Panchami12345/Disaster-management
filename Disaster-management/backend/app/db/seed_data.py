"""
Seed initial database records for DisasterShield AI
Creates users (Authority and Citizen), sample field reports, SOS beacons, and official alerts.
"""

from datetime import datetime, timezone, timedelta
from backend.app.db.database import engine, Base, SessionLocal
from backend.app.db.models import User, CitizenReport, EmergencySOS, DisasterAlert
from backend.app.services.auth_service import hash_password


def init_and_seed_db():
    print("[*] Creating database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Check if already seeded
        if db.query(User).first():
            print("[OK] Database is already initialized and seeded.")
            return

        print("[*] Seeding default users...")
        # 1. Authority Commander
        authority_user = User(
            email="officer@sdma.gov.in",
            password_hash=hash_password("admin123"),
            full_name="Commander Rajesh M.",
            role="authority",
            phone="+91-94481-22001",
            organization="Karnataka State Disaster Management Authority (KSDMA)",
            badge_number="KSDMA-INC-001"
        )
        db.add(authority_user)

        # 2. Public Citizen
        citizen_user = User(
            email="citizen@gmail.com",
            password_hash=hash_password("citizen123"),
            full_name="Ravi Kumar",
            role="citizen",
            phone="+91-98801-44332",
            organization="Kodagu District Resident"
        )
        db.add(citizen_user)
        db.commit()
        db.refresh(citizen_user)

        print("[*] Seeding citizen damage reports & rescue requests...")
        now = datetime.now(timezone.utc)
        reports = [
            CitizenReport(
                id="REP-2026-001",
                user_id=citizen_user.id,
                reporter_name="Ravi Kumar",
                reporter_phone="+91-98801-44332",
                title="Debris Flow & Mudslide Blockage on Highway Segment",
                category="LANDSLIDE",
                description="Massive mudslide has blocked both lanes of the arterial highway near Jodupala cut. Multiple commuter vehicles stranded. Slope continues to slump with active water discharge.",
                severity="CRITICAL",
                status="DISPATCHED",
                latitude=12.3382,
                longitude=75.8041,
                address="Near Jodupala Bridge Cut, NH-275",
                assigned_team="NDRF Team 4 (Sub-Inspector Gowda)",
                action_notes="Earthmoving backhoes deployed from Madikeri depot. Evacuation corridor established.",
                created_at=now - timedelta(hours=2, minutes=15)
            ),
            CitizenReport(
                id="REP-2026-002",
                user_id=citizen_user.id,
                reporter_name="Sunita Hegde",
                reporter_phone="+91-97402-11988",
                title="Residential Wall Failure & Roof Collapse",
                category="STRUCTURAL_COLLAPSE",
                description="Two adjoining tiled homes suffered major structural fissures; western load-bearing wall collapsed under continuous torrential runoff. 4 family members taking shelter in cow-shed.",
                severity="HIGH",
                status="PENDING",
                latitude=12.3340,
                longitude=75.8115,
                address="Survey No. 42, Cherambane Village",
                created_at=now - timedelta(hours=1, minutes=40)
            ),
            CitizenReport(
                id="REP-2026-003",
                user_id=None,
                reporter_name="Pramod Shetty",
                reporter_phone="+91-94490-33211",
                title="Flash Flood Inundation & Rising Water Levels",
                category="FLOOD_INUNDATION",
                description="Harangi tributary overflowed bank containment. Water depth has reached 1.2m across 6 paddy fields and lower village homesteads. Potable well contaminated.",
                severity="MEDIUM",
                status="VERIFIED",
                latitude=12.3450,
                longitude=75.7980,
                address="Lower Valley Plantation Road",
                assigned_team="Kodagu District Home Guards",
                action_notes="Warning sirens sounded; drinking water tanker dispatched.",
                created_at=now - timedelta(hours=3, minutes=10)
            ),
            CitizenReport(
                id="REP-2026-004",
                user_id=None,
                reporter_name="Ananya Rao",
                reporter_phone="+91-99805-77622",
                title="Culvert Washout - 3 Families Isolated",
                category="ROAD_BLOCK",
                description="Stream crossing culvert completely washed away. 3 families unable to cross with an infant requiring medical nebulizer supplies.",
                severity="HIGH",
                status="DISPATCHED",
                latitude=12.3290,
                longitude=75.8190,
                address="Estate Ridge Lane 3",
                assigned_team="Civil Defence QRT Unit 2",
                action_notes="Rope-line bridge being established; emergency medical kit in transit.",
                created_at=now - timedelta(minutes=50)
            ),
            CitizenReport(
                id="REP-2026-005",
                user_id=None,
                reporter_name="Ganesh Gowda",
                reporter_phone="+91-94488-55112",
                title="High-Tension Power Cable Down on Road",
                category="STRUCTURAL_COLLAPSE",
                description="Tree uprooted onto transformer line; wire hanging 2 feet above roadway.",
                severity="MEDIUM",
                status="RESOLVED",
                latitude=12.3420,
                longitude=75.8150,
                address="Koppa Cross Junction",
                assigned_team="CESC Electrical Linesmen",
                action_notes="Power isolated; wire cleared and tension re-strung. Road re-opened.",
                created_at=now - timedelta(hours=6)
            ),
        ]
        db.add_all(reports)

        print("[*] Seeding Emergency SOS Beacons...")
        sos_beacons = [
            EmergencySOS(
                id="SOS-0911-01",
                reporter_name="Kavita & Family",
                phone="+91-98800-11223",
                latitude=12.3365,
                longitude=75.8070,
                people_count=4,
                medical_need=True,
                notes="Trapped on upper terrace with elderly grandmother. Water rising.",
                status="ACTIVE",
                created_at=now - timedelta(minutes=25)
            ),
            EmergencySOS(
                id="SOS-0911-02",
                reporter_name="Worker Camp B",
                phone="+91-94482-99881",
                latitude=12.3475,
                longitude=75.7995,
                people_count=8,
                medical_need=False,
                notes="Estate mudslide approaching perimeter fence. Need transport.",
                status="DISPATCHED",
                created_at=now - timedelta(minutes=45)
            )
        ]
        db.add_all(sos_beacons)

        print("[*] Seeding official disaster alerts...")
        alerts = [
            DisasterAlert(
                id="ALT-KSDMA-01",
                source="Karnataka State Disaster Management Authority",
                title="Red Alert: Severe Inundation in Talacauvery River Corridors",
                severity="CRITICAL",
                affected_region="Kodagu District & Bhagamandala",
                description="Heavy precipitation exceeding 115mm in 24 hours. Immediate voluntary evacuation active for all households in designated Red Zones.",
                coordinates_lat=12.3375,
                coordinates_lon=75.8062,
                issued_at=now - timedelta(hours=1)
            ),
            DisasterAlert(
                id="ALT-IMD-02",
                source="India Meteorological Department",
                title="Squally Monsoon Winds & Heavy Rainfall Advisory",
                severity="WARNING",
                affected_region="Western Ghats Escarpments",
                description="Wind gusts up to 55 km/h with localized flash flooding. Avoid travel along Ghat sections after 18:00 hours.",
                coordinates_lat=12.3200,
                coordinates_lon=75.8100,
                issued_at=now - timedelta(hours=4)
            )
        ]
        db.add_all(alerts)

        db.commit()
        print("[OK] DisasterShield AI database successfully seeded with users, reports, and alerts!")
    except Exception as e:
        db.rollback()
        print(f"[!] Error seeding database: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    init_and_seed_db()
