from datetime import date

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings
from backend.app.models import (
    AIModel,
    GrantOpportunity,
    GrantTask,
    ImpactSnapshot,
    Membership,
    Organization,
    Partner,
    PartnerContact,
    Project,
    SchemaVersion,
    ResearchItem,
    Site,
    SoundClass,
    SpeciesReference,
    User,
    WeeklyReview,
)


def get_or_create(db: Session, model: type, defaults: dict | None = None, **filters):
    instance = db.scalar(select(model).filter_by(**filters))
    if instance:
        return instance
    instance = model(**filters, **(defaults or {}))
    db.add(instance)
    db.flush()
    return instance


def seed(db: Session) -> dict[str, str]:
    get_or_create(
        db,
        SchemaVersion,
        version="provisional-2026-06-10",
        defaults={
            "source": "attached planning brief",
            "notes": "Generated provisional schema; reconcile later with database_schema_ai_biodiversity.sql.",
        },
    )
    org = get_or_create(
        db,
        Organization,
        name="Urban Biodiversity Lab",
        defaults={"organization_type": "nonprofit", "website_url": "https://example.org"},
    )
    user = get_or_create(
        db,
        User,
        email="founder@example.org",
        defaults={"full_name": "MVP Founder"},
    )
    get_or_create(db, Membership, organization_id=org.id, user_id=user.id, defaults={"role": "owner"})
    project = get_or_create(
        db,
        Project,
        organization_id=org.id,
        name="Pilot Acoustic Biodiversity Survey",
        defaults={"description": "Software-first MVP pilot for upload, mock detection, dashboard, and reporting."},
    )
    site = get_or_create(
        db,
        Site,
        project_id=project.id,
        name="Riverside Test Site",
        defaults={
            "habitat_type": "urban riparian",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "location_geom_wkt": "POINT(-74.0060 40.7128)",
        },
    )

    get_or_create(
        db,
        AIModel,
        name="BirdNET Analyzer",
        version="placeholder-v1",
        defaults={"model_type": "species_classifier", "provider": "BirdNET-Team", "is_active": True},
    )
    get_or_create(
        db,
        AIModel,
        name="YAMNet",
        version="placeholder-v1",
        defaults={"model_type": "environmental_sound_classifier", "provider": "TensorFlow Hub", "is_active": True},
    )
    get_or_create(
        db,
        SpeciesReference,
        scientific_name="Turdus migratorius",
        defaults={"common_name": "American Robin", "gbif_taxon_key": 2490719, "taxon_rank": "species"},
    )
    get_or_create(
        db,
        SpeciesReference,
        scientific_name="Cardinalis cardinalis",
        defaults={"common_name": "Northern Cardinal", "gbif_taxon_key": 2490914, "taxon_rank": "species"},
    )
    get_or_create(db, SoundClass, label="Rain", defaults={"source": "YAMNet", "description": "Weather noise."})
    get_or_create(db, SoundClass, label="Traffic noise", defaults={"source": "YAMNet", "description": "Vehicle noise."})

    grant = get_or_create(
        db,
        GrantOpportunity,
        organization_id=org.id,
        name="Community Biodiversity Pilot Grant",
        defaults={"funder_name": "Placeholder Foundation", "deadline": date(2026, 9, 30), "status": "researching"},
    )
    get_or_create(
        db,
        GrantTask,
        grant_opportunity_id=grant.id,
        title="Prepare prototype impact narrative",
        defaults={"status": "todo", "due_date": date(2026, 8, 15)},
    )
    partner = get_or_create(
        db,
        Partner,
        organization_id=org.id,
        name="City Parks Department",
        defaults={"partner_type": "municipal", "status": "prospect"},
    )
    get_or_create(
        db,
        PartnerContact,
        partner_id=partner.id,
        full_name="Jordan Lee",
        defaults={"email": "jordan.lee@example.org", "role_title": "Urban Ecology Program Manager"},
    )
    get_or_create(
        db,
        ResearchItem,
        organization_id=org.id,
        title="GBIF API reference for biodiversity occurrence data",
        defaults={"source_url": "https://techdocs.gbif.org/en/openapi/", "notes": "Reference-data integration candidate."},
    )
    get_or_create(
        db,
        ImpactSnapshot,
        project_id=project.id,
        snapshot_date=date(2026, 6, 10),
        defaults={
            "species_richness": 0,
            "biodiversity_activity_score": 0,
            "noise_score": 0,
            "grant_readiness_score": 25,
            "community_value_indicators": {"pilot_sites": 1, "partner_prospects": 1},
            "metric_label": "prototype_indicator",
        },
    )
    get_or_create(
        db,
        WeeklyReview,
        organization_id=org.id,
        week_start_date=date(2026, 6, 8),
        defaults={
            "summary": "Foundation week: validate upload-to-detection workflow with mock processing.",
            "recommended_actions": {"next": ["Run first mock audio file", "Draft partner outreach"]},
        },
    )

    db.commit()
    return {"organization_id": org.id, "project_id": project.id, "site_id": site.id, "user_id": user.id}


def main() -> None:
    engine = create_engine(get_settings().database_url, future=True)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as db:
        ids = seed(db)
    print(f"Seed data ready: {ids}")


if __name__ == "__main__":
    main()
