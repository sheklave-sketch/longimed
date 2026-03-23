"""
FastAPI webhook server.
Serves:
  - Mini App API  (doctor profiles, directory, deep-link data)
  - Phase II webhooks  (Chapa, Stripe) — stubs for now
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bot.config import settings

app = FastAPI(
    title="LongiMed API",
    docs_url="/docs" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ── Mini App: Doctor directory ───────────────────────────────────────────────

@app.get("/api/doctors")
async def list_doctors(specialty: str | None = None) -> list[dict]:
    from bot.database import session_factory
    from bot.models.doctor import Doctor, RegistrationStatus
    from sqlalchemy import select

    q = select(Doctor).where(Doctor.registration_status == RegistrationStatus.APPROVED)
    if specialty:
        from bot.models.doctor import Specialty
        try:
            q = q.where(Doctor.specialty == Specialty(specialty))
        except ValueError:
            pass

    async with session_factory() as session:
        result = await session.execute(q)
        doctors = result.scalars().all()

    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialty": d.specialty.value,
            "bio": d.bio,
            "languages": d.languages,
            "rating_avg": d.rating_avg,
            "rating_count": d.rating_count,
            "is_available": d.is_available,
        }
        for d in doctors
    ]


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int) -> dict:
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    from fastapi import HTTPException

    async with session_factory() as session:
        result = await session.execute(select(Doctor).where(Doctor.id == doctor_id))
        doctor = result.scalar_one_or_none()

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "specialty": doctor.specialty.value,
        "bio": doctor.bio,
        "languages": doctor.languages,
        "rating_avg": doctor.rating_avg,
        "rating_count": doctor.rating_count,
        "is_available": doctor.is_available,
        "license_number": doctor.license_number,
        "license_document_file_id": doctor.license_document_file_id,
    }


# ── Phase II webhooks (stubs — implement in Step 16) ────────────────────────

@app.post("/webhooks/chapa")
async def chapa_webhook() -> dict:
    return {"received": True}


@app.post("/webhooks/stripe")
async def stripe_webhook() -> dict:
    return {"received": True}
