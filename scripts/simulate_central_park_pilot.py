from __future__ import annotations

import argparse
import random
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.config import get_settings
from backend.app.models import (
    AIModel,
    AudioFile,
    AuditLog,
    Base,
    Detection,
    GrantOpportunity,
    GrantTask,
    ImpactSnapshot,
    Organization,
    OutreachMessage,
    Partner,
    PartnerContact,
    ProcessingJob,
    Project,
    RawModelOutput,
    Report,
    Site,
    SpeciesReference,
    WeeklyReview,
)
from database.seed.seed_data import get_or_create, seed


PROJECT_NAME = "Central Park Acoustic Biodiversity Pilot Simulation"
PROJECT_EXTERNAL_ID = "sim-central-park-2026"
SIMULATION_TAG = "central_park_pilot_simulation_v1"

SITES = [
    ("North Woods", "mature woodland / ravine", 40.7975, -73.9567),
    ("The Ramble", "woodland understory / migratory stopover", 40.7772, -73.9694),
    ("Jacqueline Kennedy Onassis Reservoir", "open water edge", 40.7851, -73.9590),
    ("Sheep Meadow", "open lawn / urban edge", 40.7711, -73.9741),
    ("Hallett Nature Sanctuary", "restored woodland / pond edge", 40.7665, -73.9733),
]

SPECIES = [
    ("Turdus migratorius", "American Robin"),
    ("Cardinalis cardinalis", "Northern Cardinal"),
    ("Cyanocitta cristata", "Blue Jay"),
    ("Agelaius phoeniceus", "Red-winged Blackbird"),
    ("Zenaida macroura", "Mourning Dove"),
    ("Passer domesticus", "House Sparrow"),
    ("Baeolophus bicolor", "Tufted Titmouse"),
    ("Dumetella carolinensis", "Gray Catbird"),
    ("Quiscalus quiscula", "Common Grackle"),
    ("Buteo jamaicensis", "Red-tailed Hawk"),
    ("Branta canadensis", "Canada Goose"),
    ("Anas platyrhynchos", "Mallard"),
    ("Melospiza melodia", "Song Sparrow"),
    ("Dryobates pubescens", "Downy Woodpecker"),
]

SITE_SPECIES_WEIGHTS = {
    "North Woods": ["American Robin", "Northern Cardinal", "Blue Jay", "Tufted Titmouse", "Downy Woodpecker", "Gray Catbird"],
    "The Ramble": ["American Robin", "Gray Catbird", "Song Sparrow", "Northern Cardinal", "Blue Jay", "Common Grackle"],
    "Jacqueline Kennedy Onassis Reservoir": ["Canada Goose", "Mallard", "Red-winged Blackbird", "American Robin", "Common Grackle"],
    "Sheep Meadow": ["House Sparrow", "Mourning Dove", "American Robin", "Common Grackle", "Blue Jay"],
    "Hallett Nature Sanctuary": ["Northern Cardinal", "Song Sparrow", "American Robin", "Gray Catbird", "Red-tailed Hawk"],
}

SOUND_CLASSES = ["Traffic noise", "Human voices", "Wind", "Rain"]


def _species_map(db: Session) -> dict[str, SpeciesReference]:
    refs = {}
    for scientific_name, common_name in SPECIES:
        refs[common_name] = get_or_create(
            db,
            SpeciesReference,
            scientific_name=scientific_name,
            defaults={"common_name": common_name, "taxon_rank": "species"},
        )
    return refs


def _reset_project_data(db: Session, project: Project) -> None:
    site_ids = list(db.scalars(select(Site.id).where(Site.project_id == project.id)))
    if not site_ids:
        return
    audio_ids = list(db.scalars(select(AudioFile.id).where(AudioFile.site_id.in_(site_ids))))
    job_ids = list(db.scalars(select(ProcessingJob.id).where(ProcessingJob.audio_file_id.in_(audio_ids)))) if audio_ids else []
    if job_ids:
        db.execute(delete(Detection).where(Detection.processing_job_id.in_(job_ids)))
        db.execute(delete(RawModelOutput).where(RawModelOutput.processing_job_id.in_(job_ids)))
        db.execute(delete(ProcessingJob).where(ProcessingJob.id.in_(job_ids)))
    if audio_ids:
        db.execute(delete(AudioFile).where(AudioFile.id.in_(audio_ids)))
    db.execute(delete(Site).where(Site.id.in_(site_ids)))
    db.execute(delete(Report).where(Report.project_id == project.id))
    db.execute(delete(ImpactSnapshot).where(ImpactSnapshot.project_id == project.id))
    db.flush()


def _review_status(rng: random.Random, confidence: float) -> str:
    if confidence >= 0.72:
        return rng.choices(["confirmed", "unreviewed", "rejected"], weights=[0.62, 0.34, 0.04])[0]
    if confidence >= 0.52:
        return rng.choices(["confirmed", "unreviewed", "rejected"], weights=[0.38, 0.5, 0.12])[0]
    return rng.choices(["confirmed", "unreviewed", "rejected"], weights=[0.18, 0.56, 0.26])[0]


def simulate(db: Session, recordings_per_site: int = 20, seed_value: int = 42) -> dict[str, object]:
    rng = random.Random(seed_value)
    ids = seed(db)
    org = db.get(Organization, ids["organization_id"])
    birdnet = get_or_create(
        db,
        AIModel,
        name="BirdNET Analyzer",
        version="simulated-pilot-v1",
        defaults={"model_type": "species_classifier", "provider": "BirdNET-Team", "is_active": True},
    )
    species_by_common = _species_map(db)

    project = get_or_create(
        db,
        Project,
        external_id=PROJECT_EXTERNAL_ID,
        defaults={
            "organization_id": org.id,
            "name": PROJECT_NAME,
            "description": "Simulated 30-day Central Park acoustic biodiversity pilot for partner rehearsal. Not field-validated.",
            "status": "active",
        },
    )
    project.name = PROJECT_NAME
    project.description = "Simulated 30-day Central Park acoustic biodiversity pilot for partner rehearsal. Not field-validated."
    project.status = "active"
    _reset_project_data(db, project)

    created_sites: list[Site] = []
    for name, habitat, latitude, longitude in SITES:
        site = Site(
            project_id=project.id,
            external_id=f"sim-central-park-{name.lower().replace(' ', '-').replace('/', '-')}",
            name=name,
            habitat_type=habitat,
            latitude=latitude,
            longitude=longitude,
            location_geom_wkt=f"POINT({longitude} {latitude})",
        )
        db.add(site)
        created_sites.append(site)
    db.flush()

    start = datetime(2026, 5, 1, 5, 30, tzinfo=UTC)
    total_audio = 0
    total_species_detections = 0
    total_sound_detections = 0
    confirmed = 0

    for site in created_sites:
        focus_species = SITE_SPECIES_WEIGHTS[site.name]
        for index in range(recordings_per_site):
            day_offset = (index * 2 + rng.randint(0, 1)) % 30
            minute_offset = rng.choice([0, 15, 30, 45])
            recorded_at = start + timedelta(days=day_offset, minutes=minute_offset)
            duration = rng.choice([90.0, 120.0, 150.0])
            audio = AudioFile(
                site_id=site.id,
                file_name=f"{site.name.lower().replace(' ', '-')}-{index + 1:02d}.wav",
                idempotency_key=f"{SIMULATION_TAG}:{site.name}:{index + 1}",
                storage_uri=f"simulation://central-park/{site.name.lower().replace(' ', '-')}/{index + 1:02d}.wav",
                content_type="audio/wav",
                duration_seconds=duration,
                recorded_at=recorded_at,
                status="processed",
            )
            db.add(audio)
            db.flush()
            job = ProcessingJob(
                audio_file_id=audio.id,
                status="completed",
                job_type="birdnet_analysis",
                started_at=recorded_at + timedelta(minutes=2),
                completed_at=recorded_at + timedelta(minutes=3, seconds=rng.randint(5, 45)),
            )
            db.add(job)
            db.flush()

            species_count = rng.randint(3, 7)
            chosen_species = rng.choices(focus_species, k=species_count)
            raw_results = []
            for detection_index, common_name in enumerate(chosen_species):
                species = species_by_common[common_name]
                confidence = round(rng.uniform(0.34, 0.92), 3)
                start_seconds = float(rng.randint(0, int(max(1, duration - 8))))
                end_seconds = min(duration, start_seconds + rng.choice([2.5, 3.0, 4.0, 5.0]))
                review_status = _review_status(rng, confidence)
                if review_status == "confirmed":
                    confirmed += 1
                db.add(
                    Detection(
                        processing_job_id=job.id,
                        audio_file_id=audio.id,
                        ai_model_id=birdnet.id,
                        species_reference_id=species.id,
                        detection_type="species",
                        label=common_name,
                        confidence=confidence,
                        start_seconds=start_seconds,
                        end_seconds=end_seconds,
                        review_status=review_status,
                    )
                )
                raw_results.append(
                    {
                        "label": f"{species.scientific_name}_{common_name}",
                        "confidence": confidence,
                        "start_seconds": start_seconds,
                        "end_seconds": end_seconds,
                        "review_status": review_status,
                    }
                )
                total_species_detections += 1

            if rng.random() < 0.64:
                sound_label = rng.choice(SOUND_CLASSES)
                db.add(
                    Detection(
                        processing_job_id=job.id,
                        audio_file_id=audio.id,
                        ai_model_id=None,
                        detection_type="sound_class",
                        label=sound_label,
                        confidence=round(rng.uniform(0.4, 0.88), 3),
                        start_seconds=0.0,
                        end_seconds=min(duration, 10.0),
                        review_status="unreviewed",
                    )
                )
                total_sound_detections += 1

            db.add(
                RawModelOutput(
                    processing_job_id=job.id,
                    audio_file_id=audio.id,
                    ai_model_id=birdnet.id,
                    output_format="simulation_json",
                    payload={
                        "contract": "central_park_pilot_simulation.v1",
                        "mode": "simulated_pilot",
                        "configured": False,
                        "source": "Deterministic simulated BirdNET-like output for partner demo rehearsal",
                        "simulation_tag": SIMULATION_TAG,
                        "site": site.name,
                        "recorded_at": recorded_at.isoformat(),
                        "results": raw_results,
                    },
                )
            )
            total_audio += 1

    db.add(
        Report(
            project_id=project.id,
            title="Central Park Pilot Simulation Summary",
            report_type="pilot_simulation",
            status="draft",
            storage_uri="simulation://central-park/report-shell",
        )
    )
    db.add(
        ImpactSnapshot(
            project_id=project.id,
            snapshot_date=date(2026, 5, 30),
            species_richness=len(SPECIES),
            biodiversity_activity_score=82.0,
            noise_score=38.0,
            grant_readiness_score=68.0,
            metric_label="prototype_indicator_simulation",
            community_value_indicators={
                "simulation": True,
                "recordings": total_audio,
                "sites": len(created_sites),
                "confirmed_candidate_detections": confirmed,
                "partner_target": "Central Park Conservancy / NYC parks ecology stakeholders",
            },
        )
    )
    partner = get_or_create(
        db,
        Partner,
        organization_id=org.id,
        name="Central Park Conservancy",
        defaults={"partner_type": "park conservancy", "status": "target_partner"},
    )
    partner.status = "target_partner"
    get_or_create(
        db,
        PartnerContact,
        partner_id=partner.id,
        full_name="Central Park Pilot Contact",
        defaults={"role_title": "Prospective ecology or conservation programs lead"},
    )
    get_or_create(
        db,
        GrantOpportunity,
        organization_id=org.id,
        name="Urban Acoustic Biodiversity Pilot Funding Package",
        defaults={"funder_name": "Conservation and climate resilience funders", "deadline": date(2026, 9, 30), "status": "researching"},
    )
    db.add(
        OutreachMessage(
            organization_id=org.id,
            partner_id=partner.id,
            subject="BioSignal Central Park acoustic biodiversity pilot proposal",
            body=(
                "Draft: BioSignal is seeking a Central Park pilot partner to validate a 30-day acoustic biodiversity "
                "workflow across 3-5 habitats using WAV recordings, BirdNET candidate detections, human review, CSV exports, "
                "and a partner-ready pilot report. Current Central Park dataset is simulated for rehearsal only."
            ),
            status="draft",
        )
    )
    db.add(
        WeeklyReview(
            organization_id=org.id,
            week_start_date=date(2026, 5, 25),
            summary="Central Park pilot simulation created for partner-demo rehearsal. Replace simulation with real field recordings after partner approval.",
            recommended_actions={
                "next": [
                    "Secure permission and protocol approval",
                    "Collect 50-100 real WAV recordings",
                    "Run real BirdNET inference with site/date context",
                    "Review a representative detection subset",
                ]
            },
        )
    )
    db.add(
        AuditLog(
            action="simulate_pilot",
            entity_type="project",
            entity_id=project.id,
            metadata_json={"simulation_tag": SIMULATION_TAG, "recordings": total_audio, "sites": len(created_sites)},
        )
    )
    db.commit()
    return {
        "project_id": project.id,
        "project_name": project.name,
        "simulation_tag": SIMULATION_TAG,
        "sites": len(created_sites),
        "audio_files": total_audio,
        "species_detections": total_species_detections,
        "sound_detections": total_sound_detections,
        "confirmed_species_detections": confirmed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a deterministic Central Park pilot simulation dataset.")
    parser.add_argument("--recordings-per-site", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    engine = create_engine(get_settings().database_url, future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    with session_factory() as db:
        summary = simulate(db, recordings_per_site=args.recordings_per_site, seed_value=args.seed)
    print("Central Park pilot simulation ready:")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    print("Open http://127.0.0.1:8000/app/ and select the Central Park simulation project.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
