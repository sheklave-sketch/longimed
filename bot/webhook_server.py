"""
FastAPI webhook server.
Serves:
  - Mini App API  (doctor profiles, directory, Q&A feed)
  - Phase II webhooks  (Chapa, Stripe) — stubs for now
"""
from __future__ import annotations

import logging

import httpx
import os
import uuid

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from bot.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title="LongiMed API",
    docs_url="/docs" if not settings.is_production else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Static file serving for uploads ──────────────────────────────────────────

UPLOAD_DIR = "/app/uploads" if os.path.exists("/app") else os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a photo/document. Returns the public URL."""
    if not file.content_type or not file.content_type.startswith(("image/", "application/pdf")):
        raise HTTPException(status_code=400, detail="Only images and PDFs are accepted")

    if file.size and file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Return relative URL — served by static mount above
    return {"url": f"/uploads/{filename}", "filename": filename}


# ── Telegram notification helper ─────────────────────────────────────────────

async def _tg_notify(chat_id: int, text: str):
    """Send a Telegram message from FastAPI (no bot instance)."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(
                f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage",
                json={"chat_id": chat_id, "text": text},
            )
    except Exception:
        pass


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── User role check ───────────────────────────────────────────────────────────

@app.get("/api/user/role/{telegram_id}")
async def get_user_role(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    is_admin = telegram_id in settings.admin_ids
    is_doctor = False

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Doctor).where(
                    Doctor.telegram_id == telegram_id,
                    Doctor.is_verified.is_(True),
                )
            )
            is_doctor = result.scalar_one_or_none() is not None
    except Exception:
        pass

    return {"is_doctor": is_doctor, "is_admin": is_admin}


# ── Mini App: Doctor directory ───────────────────────────────────────────────

@app.get("/api/doctors")
async def list_doctors(specialty: str | None = None):
    """Public doctor directory for Mini App."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select

    try:
        q = select(Doctor).where(Doctor.is_verified.is_(True))
        if specialty:
            from bot.models.doctor import Specialty
            try:
                q = q.where(Doctor.specialty == Specialty(specialty))
            except ValueError:
                pass

        async with session_factory() as session:
            result = await session.execute(q)
            doctors = result.scalars().all()
    except Exception:
        logger.exception("Failed to list doctors")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
            "specialties": d.specialties or [d.specialty.value if hasattr(d.specialty, "value") else d.specialty],
            "bio": d.bio,
            "is_available": d.is_available,
            "rating_avg": round(d.rating_avg, 2),
            "rating_count": d.rating_count,
            "languages": d.languages,
            "profile_photo_url": d.profile_photo_file_id,
        }
        for d in doctors
    ]


@app.get("/api/doctors/{doctor_id}")
async def get_doctor(doctor_id: int):
    """Public doctor profile for Mini App."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor

    try:
        async with session_factory() as session:
            doctor = await session.get(Doctor, doctor_id)
    except Exception:
        logger.exception("Failed to fetch doctor %d", doctor_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    if not doctor or not doctor.is_verified:
        raise HTTPException(status_code=404, detail="Doctor not found")

    return {
        "id": doctor.id,
        "full_name": doctor.full_name,
        "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else doctor.specialty,
        "specialties": doctor.specialties or [doctor.specialty.value if hasattr(doctor.specialty, "value") else doctor.specialty],
        "bio": doctor.bio,
        "license_number": doctor.license_number,
        "is_available": doctor.is_available,
        "rating_avg": round(doctor.rating_avg, 2),
        "rating_count": doctor.rating_count,
        "languages": doctor.languages,
        "profile_photo_url": doctor.profile_photo_file_id,
    }


# ── Mini App: Public Q&A feed ───────────────────────────────────────────────

@app.get("/api/questions")
async def list_questions(limit: int = 20, offset: int = 0):
    """Public Q&A feed for Mini App."""
    from bot.database import session_factory
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select

    try:
        async with session_factory() as session:
            result = await session.execute(
                select(Question).where(
                    Question.status.in_([QuestionStatus.APPROVED, QuestionStatus.ANSWERED])
                ).order_by(Question.created_at.desc()).offset(offset).limit(limit)
            )
            questions = result.scalars().all()
    except Exception:
        logger.exception("Failed to list questions")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": q.id,
            "category": q.category.value if hasattr(q.category, "value") else q.category,
            "text": q.text,
            "is_anonymous": q.is_anonymous,
            "status": q.status.value,
            "answer_text": q.answer_text,
            "created_at": str(q.created_at),
            "answered_at": str(q.answered_at) if q.answered_at else None,
        }
        for q in questions
    ]


# ── Doctor Dashboard ──────────────────────────────────────────────────────

@app.get("/api/doctors/dashboard/{telegram_id}")
async def doctor_dashboard(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS, SessionStatus
    from bot.models.doctor_earnings import DoctorEarnings, EarningsStatus
    from sqlalchemy import select, func

    try:
        async with session_factory() as session:
            doc_r = await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id, Doctor.is_verified.is_(True))
            )
            doctor = doc_r.scalar_one_or_none()
            if not doctor:
                raise HTTPException(status_code=404, detail="Not found")

            total = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id)
            )).scalar() or 0
            active = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id, CS.status == SessionStatus.ACTIVE)
            )).scalar() or 0
            pending = (await session.execute(
                select(func.count()).select_from(CS).where(CS.doctor_id == doctor.id, CS.status == SessionStatus.AWAITING_DOCTOR)
            )).scalar() or 0
            pending_earn = (await session.execute(
                select(func.coalesce(func.sum(DoctorEarnings.net_etb), 0)).where(
                    DoctorEarnings.doctor_id == doctor.id, DoctorEarnings.status == EarningsStatus.PENDING)
            )).scalar() or 0
            paid_earn = (await session.execute(
                select(func.coalesce(func.sum(DoctorEarnings.net_etb), 0)).where(
                    DoctorEarnings.doctor_id == doctor.id, DoctorEarnings.status == EarningsStatus.PAID)
            )).scalar() or 0
            recent = (await session.execute(
                select(CS).where(CS.doctor_id == doctor.id).order_by(CS.created_at.desc()).limit(10)
            )).scalars().all()
    except HTTPException:
        raise
    except Exception:
        logger.exception("Dashboard error")
        raise HTTPException(status_code=500, detail="Error")

    return {
        "doctor": {
            "id": doctor.id,
            "full_name": doctor.full_name,
            "specialty": doctor.specialty.value if hasattr(doctor.specialty, "value") else doctor.specialty,
            "specialties": doctor.specialties or [],
            "languages": doctor.languages or [],
            "bio": doctor.bio or "",
            "sex": doctor.sex.value if doctor.sex and hasattr(doctor.sex, "value") else None,
            "sub_specialization": doctor.sub_specialization or "",
            "profile_photo_url": doctor.profile_photo_file_id,
            "is_available": doctor.is_available,
            "rating_avg": round(doctor.rating_avg, 2),
            "rating_count": doctor.rating_count,
        },
        "stats": {
            "total_sessions": total, "active_sessions": active, "pending_queue": pending,
            "pending_earnings": float(pending_earn), "paid_earnings": float(paid_earn),
        },
        "recent_sessions": [
            {"id": s.id, "status": s.status.value if hasattr(s.status, "value") else s.status,
             "issue_description": s.issue_description[:100], "created_at": str(s.created_at)}
            for s in recent
        ],
    }


@app.post("/api/doctors/toggle-availability/{telegram_id}")
async def toggle_availability(telegram_id: int):
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        r = await session.execute(select(Doctor).where(Doctor.telegram_id == telegram_id, Doctor.is_verified.is_(True)))
        doctor = r.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404)
        doctor.is_available = not doctor.is_available
        await session.commit()
    return {"is_available": doctor.is_available}


# ── Admin Dashboard ──────────────────────────────────────────────────────

@app.get("/api/admin/dashboard/{telegram_id}")
async def admin_dashboard(telegram_id: int):
    if telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Forbidden")
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.doctor import Doctor, RegistrationStatus
    from bot.models.question import Question, QuestionStatus
    from bot.models.session import Session as CS
    from bot.models.payment import Payment
    from sqlalchemy import select, func
    try:
        async with session_factory() as session:
            tu = (await session.execute(select(func.count()).select_from(User))).scalar() or 0
            td = (await session.execute(select(func.count()).select_from(Doctor).where(Doctor.is_verified.is_(True)))).scalar() or 0
            tq = (await session.execute(select(func.count()).select_from(Question))).scalar() or 0
            ts = (await session.execute(select(func.count()).select_from(CS))).scalar() or 0
            pd = (await session.execute(select(func.count()).select_from(Doctor).where(Doctor.registration_status == RegistrationStatus.PENDING))).scalar() or 0
            pq = (await session.execute(select(func.count()).select_from(Question).where(Question.status == QuestionStatus.PENDING))).scalar() or 0
            pending_docs = (await session.execute(select(Doctor).where(Doctor.registration_status == RegistrationStatus.PENDING).order_by(Doctor.applied_at.desc()))).scalars().all()
            payments = (await session.execute(select(Payment).order_by(Payment.created_at.desc()).limit(20))).scalars().all()
    except Exception:
        logger.exception("Admin dashboard error")
        raise HTTPException(status_code=500)
    return {
        "stats": {"total_users": tu, "total_doctors": td, "total_questions": tq, "total_sessions": ts, "pending_doctors": pd, "pending_questions": pq},
        "pending_doctors": [
            {"id": d.id, "full_name": d.full_name, "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
             "license_number": d.license_number, "applied_at": str(d.applied_at) if d.applied_at else ""}
            for d in pending_docs
        ],
        "recent_payments": [
            {"id": p.id, "amount_etb": float(p.amount_etb) if p.amount_etb else 0,
             "status": p.status.value if hasattr(p.status, "value") else p.status,
             "created_at": str(p.created_at), "user_telegram_id": p.user_id}
            for p in payments
        ],
    }


# ── Profile editing ─────────────────────────────────────────────────────────
# NOTE: These specific routes MUST be registered before the
# `/api/admin/doctors/{doctor_id}/{action}` catch-all below — FastAPI matches
# routes in registration order, and the catch-all would otherwise swallow
# `/profile` requests with action="profile" and reject them as 400.

_PROFILE_EDITABLE_FIELDS = {
    "full_name", "bio", "sub_specialization", "languages",
    "specialty", "specialties", "sex", "profile_photo_url",
}
_ADMIN_ONLY_FIELDS = {
    "license_number", "is_verified", "is_available", "telegram_id",
    "max_concurrent_patients",
}


def _apply_doctor_updates(doctor, body, allowed):
    from bot.models.doctor import Specialty, Sex
    changed = []
    for field, value in body.items():
        if field not in allowed:
            continue
        if field == "profile_photo_url":
            doctor.profile_photo_file_id = value or None
            changed.append(field)
        elif field == "specialty" and value:
            try:
                doctor.specialty = Specialty(value)
                changed.append(field)
            except ValueError:
                continue
        elif field == "sex":
            doctor.sex = Sex(value) if value else None
            changed.append(field)
        elif field == "specialties":
            doctor.specialties = list(value or [])
            changed.append(field)
        elif field == "languages":
            if value:
                doctor.languages = list(value)
                changed.append(field)
        elif field in {"bio", "full_name", "sub_specialization", "license_number"}:
            setattr(doctor, field, (value or "").strip() or (None if field != "full_name" else doctor.full_name))
            changed.append(field)
        elif field == "telegram_id":
            doctor.telegram_id = int(value) if value else None
            changed.append(field)
        elif field in {"is_verified", "is_available"}:
            setattr(doctor, field, bool(value))
            changed.append(field)
        elif field == "max_concurrent_patients" and value:
            doctor.max_concurrent_patients = int(value)
            changed.append(field)
    return changed


@app.post("/api/doctors/{telegram_id}/profile")
async def update_own_profile(telegram_id: int, request: Request):
    """Doctor self-edit. The telegram_id in the path must match a verified doctor."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    body = await request.json()
    async with session_factory() as session:
        result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id, Doctor.is_verified.is_(True))
        )
        doctor = result.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Verified doctor not found")
        changed = _apply_doctor_updates(doctor, body, _PROFILE_EDITABLE_FIELDS)
        await session.commit()
    return {"status": "ok", "changed": changed}


@app.post("/api/admin/doctors/{doctor_id}/profile")
async def admin_update_profile(doctor_id: int, request: Request):
    """Admin edit any doctor. Requires admin_telegram_id in body matching settings.admin_ids."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    body = await request.json()
    admin_tg = body.pop("admin_telegram_id", None)
    if not admin_tg or int(admin_tg) not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Admin only")
    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404)
        changed = _apply_doctor_updates(
            doctor, body, _PROFILE_EDITABLE_FIELDS | _ADMIN_ONLY_FIELDS
        )
        await session.commit()
    return {"status": "ok", "changed": changed}


@app.get("/api/admin/doctors")
async def admin_list_doctors(admin_telegram_id: int):
    """Full doctor list for admin management UI."""
    if admin_telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403)
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    async with session_factory() as session:
        rows = (await session.execute(
            select(Doctor).order_by(Doctor.is_verified.desc(), Doctor.full_name.asc())
        )).scalars().all()
    return [
        {
            "id": d.id,
            "telegram_id": d.telegram_id,
            "full_name": d.full_name,
            "license_number": d.license_number,
            "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
            "specialties": d.specialties or [],
            "languages": d.languages or [],
            "bio": d.bio or "",
            "sex": d.sex.value if d.sex and hasattr(d.sex, "value") else None,
            "sub_specialization": d.sub_specialization or "",
            "profile_photo_url": d.profile_photo_file_id,
            "is_verified": d.is_verified,
            "is_available": d.is_available,
            "registration_status": d.registration_status.value if hasattr(d.registration_status, "value") else d.registration_status,
            "rating_avg": float(d.rating_avg or 0),
            "rating_count": d.rating_count or 0,
        }
        for d in rows
    ]


@app.post("/api/admin/doctors/{doctor_id}/{action}")
async def admin_doctor_action(doctor_id: int, action: str):
    if action not in ("approve", "reject"):
        raise HTTPException(status_code=400)
    from bot.database import session_factory
    from bot.models.doctor import Doctor, RegistrationStatus
    async with session_factory() as session:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            raise HTTPException(status_code=404)
        if action == "approve":
            doctor.is_verified = True
            doctor.registration_status = RegistrationStatus.APPROVED
        else:
            doctor.registration_status = RegistrationStatus.REJECTED
        await session.commit()
    return {"status": "ok", "action": action}


# ── POST /api/questions — Submit a public question ───────────────────────

@app.post("/api/questions")
async def submit_question(request: Request):
    """Submit a public question for moderation."""
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.question import Question, QuestionStatus
    from bot.models.doctor import Specialty
    from sqlalchemy import select

    body = await request.json()
    telegram_id = body.get("telegram_id")
    category = body.get("category")
    text = body.get("text")
    is_anonymous = body.get("is_anonymous", False)

    if not telegram_id or not category or not text:
        raise HTTPException(status_code=400, detail="telegram_id, category, and text are required")

    try:
        async with session_factory() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            try:
                cat_enum = Specialty(category)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid category: {category}")

            question = Question(
                user_id=user.id,
                category=cat_enum,
                text=text,
                is_anonymous=is_anonymous,
                status=QuestionStatus.PENDING,
            )
            session.add(question)
            await session.commit()
            await session.refresh(question)
            q_id = question.id
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to submit question")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Notify admins
    for admin_id in settings.admin_ids:
        await _tg_notify(
            admin_id,
            f"New question #{q_id} pending approval.\nCategory: {category}\nText: {text[:200]}",
        )

    return {"id": q_id, "status": "pending"}


# ── GET /api/questions/{question_id} — Single question + follow-ups ──────

@app.get("/api/questions/{question_id}")
async def get_question(question_id: int):
    """Get a single question with its approved follow-ups."""
    from bot.database import session_factory
    from bot.models.question import Question
    from bot.models.follow_up import FollowUp, FollowUpStatus
    from bot.models.doctor import Doctor
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    try:
        async with session_factory() as session:
            question = (await session.execute(
                select(Question).where(Question.id == question_id)
            )).scalar_one_or_none()
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            follow_ups = (await session.execute(
                select(FollowUp).where(
                    FollowUp.question_id == question_id,
                    FollowUp.status == FollowUpStatus.APPROVED,
                ).order_by(FollowUp.created_at.asc())
            )).scalars().all()

            # Get doctor name if answered
            doctor_name = None
            if question.answered_by_doctor_id:
                doctor = await session.get(Doctor, question.answered_by_doctor_id)
                if doctor:
                    doctor_name = doctor.full_name
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch question %d", question_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    return {
        "id": question.id,
        "category": question.category.value if hasattr(question.category, "value") else question.category,
        "text": question.text,
        "is_anonymous": question.is_anonymous,
        "status": question.status.value,
        "answer_text": question.answer_text,
        "answered_by": doctor_name,
        "created_at": str(question.created_at),
        "answered_at": str(question.answered_at) if question.answered_at else None,
        "follow_ups": [
            {
                "id": f.id,
                "text": f.text,
                "is_anonymous": f.is_anonymous,
                "created_at": str(f.created_at),
            }
            for f in follow_ups
        ],
    }


# ── POST /api/questions/{question_id}/follow-ups — Submit a follow-up ────

@app.post("/api/questions/{question_id}/follow-ups")
async def submit_follow_up(question_id: int, request: Request):
    """Submit a follow-up to an existing question."""
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.question import Question
    from bot.models.follow_up import FollowUp, FollowUpStatus
    from sqlalchemy import select

    body = await request.json()
    telegram_id = body.get("telegram_id")
    text = body.get("text")
    is_anonymous = body.get("is_anonymous", False)

    if not telegram_id or not text:
        raise HTTPException(status_code=400, detail="telegram_id and text are required")

    try:
        async with session_factory() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            question = await session.get(Question, question_id)
            if not question:
                raise HTTPException(status_code=404, detail="Question not found")

            follow_up = FollowUp(
                question_id=question_id,
                user_id=user.id,
                text=text,
                is_anonymous=is_anonymous,
                status=FollowUpStatus.PENDING,
            )
            session.add(follow_up)
            await session.commit()
            await session.refresh(follow_up)
            fu_id = follow_up.id
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to submit follow-up for question %d", question_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    return {"id": fu_id, "status": "pending"}


# ── POST /api/sessions/book — Book a consultation ────────────────────────

@app.post("/api/sessions/book")
async def book_session(request: Request):
    """Book a private consultation session."""
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS, SessionPackage, SessionStatus, SessionMode
    from bot.models.payment import Payment, PaymentProvider, PaymentStatus
    from sqlalchemy import select
    from decimal import Decimal

    body = await request.json()
    telegram_id = body.get("telegram_id")
    package = body.get("package")
    specialty = body.get("specialty")
    doctor_id = body.get("doctor_id")
    issue_description = body.get("issue_description")
    is_anonymous = body.get("is_anonymous", False)

    if not telegram_id or not package or not issue_description:
        raise HTTPException(status_code=400, detail="telegram_id, package, and issue_description are required")

    # Normalize case — Mini App sends uppercase, bot sends lowercase
    package = package.lower() if package else package
    if package not in ("free_trial", "single"):
        raise HTTPException(status_code=400, detail="package must be 'free_trial' or 'single'")

    try:
        async with session_factory() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Check free trial eligibility
            if package == "free_trial" and user.free_trial_used:
                raise HTTPException(status_code=400, detail="Free trial already used")

            # Validate doctor if provided
            doctor = None
            if doctor_id:
                doctor = await session.get(Doctor, doctor_id)
                if not doctor or not doctor.is_verified:
                    raise HTTPException(status_code=404, detail="Doctor not found or not verified")

            session_mode = SessionMode.RELAY if is_anonymous else SessionMode.TOPIC

            if package == "free_trial":
                pkg_enum = SessionPackage.FREE_TRIAL
                status = SessionStatus.AWAITING_DOCTOR
                # Mark free trial as used
                user.free_trial_used = True
                payment_id = None
            else:
                pkg_enum = SessionPackage.SINGLE
                status = SessionStatus.PENDING_APPROVAL
                # Create payment record
                pay = Payment(
                    user_id=user.id,
                    amount_etb=Decimal("500.00"),
                    provider=PaymentProvider.MANUAL,
                    status=PaymentStatus.PENDING,
                )
                session.add(pay)
                await session.flush()
                payment_id = pay.id

            cs = CS(
                user_id=user.id,
                doctor_id=doctor_id,
                package=pkg_enum,
                status=status,
                session_mode=session_mode,
                issue_description=issue_description,
                is_anonymous=is_anonymous,
                payment_id=payment_id,
            )
            session.add(cs)
            await session.commit()
            await session.refresh(cs)
            session_id = cs.id
            final_status = cs.status.value
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to book session")
        raise HTTPException(status_code=500, detail="Internal server error")

    from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
    from bot.i18n import t
    bot = Bot(settings.telegram_bot_token)

    # Get patient language for translated notifications
    patient_lang = "en"
    try:
        async with session_factory() as s:
            u = (await s.execute(select(User).where(User.telegram_id == telegram_id))).scalar_one_or_none()
            if u:
                patient_lang = u.language
    except Exception:
        pass

    if package == "free_trial" and doctor_id:
        # Free trial: notify doctor with Accept/Decline buttons
        if doctor and doctor.telegram_id:
            mode_label = "Anonymous (relay)" if is_anonymous else "Named (room)"
            kb = InlineKeyboardMarkup([[
                InlineKeyboardButton("\u2705 Accept Session", callback_data=f"accept_session:{session_id}"),
                InlineKeyboardButton("\u274c Decline", callback_data=f"decline_session:{session_id}"),
            ]])
            try:
                await bot.send_message(
                    chat_id=doctor.telegram_id,
                    text=(
                        f"New consultation request (#{session_id})\n\n"
                        f"Mode: {mode_label}\n"
                        f"Issue: {issue_description[:200]}"
                    ),
                    reply_markup=kb,
                )
            except Exception as exc:
                logger.error("Failed to notify doctor: %s", exc)
        elif doctor and not doctor.telegram_id:
            # Doctor has no Telegram linked — alert admins
            for admin_id in settings.admin_ids:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"⚠️ Session #{session_id}: Dr. {doctor.full_name} has no Telegram linked.",
                    )
                except Exception:
                    pass

        # Notify patient in bot
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=t("session_awaiting", patient_lang),
            )
        except Exception:
            pass

    elif package == "single":
        # Paid: notify admins with Confirm/Reject payment buttons
        pay_kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("\u2705 Confirm Payment (500 ETB)", callback_data=f"confirmpay:{telegram_id}:500"),
            InlineKeyboardButton("\u274c Reject", callback_data=f"rejectpay:{telegram_id}:{session_id}"),
        ]])
        for admin_id in settings.admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=(
                        f"\U0001f4b0 Pending payment for session #{session_id}\n"
                        f"Patient TG ID: {telegram_id}\n"
                        f"Amount: 500 ETB"
                    ),
                    reply_markup=pay_kb,
                )
            except Exception:
                pass

        # Notify patient with payment instructions in their language
        try:
            await bot.send_message(
                chat_id=telegram_id,
                text=t("payment_manual_instructions", patient_lang,
                      amount="500",
                      bank_name="Commercial Bank of Ethiopia",
                      account_number="1000XXXXXXXX",
                      account_name="LongiMed Health Services"),
            )
        except Exception:
            pass

    result = {"session_id": session_id, "status": final_status}
    if package == "single":
        result["payment_instructions"] = t("payment_manual_instructions", patient_lang,
            amount="500", bank_name="Commercial Bank of Ethiopia",
            account_number="1000XXXXXXXX", account_name="LongiMed Health Services")
    return result


# ── GET /api/sessions/my/{telegram_id} — User session history ────────────

@app.get("/api/sessions/my/{telegram_id}")
async def my_sessions(telegram_id: int):
    """Get a user's session history (as patient and/or doctor)."""
    from bot.database import session_factory
    from bot.models.user import User
    from bot.models.doctor import Doctor
    from bot.models.session import Session as CS
    from sqlalchemy import select, or_

    try:
        async with session_factory() as session:
            user = (await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Check if user is also a doctor
            doctor = (await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id)
            )).scalar_one_or_none()

            conditions = [CS.user_id == user.id]
            if doctor:
                conditions.append(CS.doctor_id == doctor.id)

            sessions_list = (await session.execute(
                select(CS).where(or_(*conditions)).order_by(CS.created_at.desc()).limit(50)
            )).scalars().all()

            # Preload doctor/user names for display
            result = []
            for s in sessions_list:
                entry = {
                    "id": s.id,
                    "status": s.status.value if hasattr(s.status, "value") else s.status,
                    "package": s.package.value if hasattr(s.package, "value") else s.package,
                    "created_at": str(s.created_at),
                    "issue_description": s.issue_description[:100] if s.issue_description else "",
                    "role": "doctor" if (doctor and s.doctor_id == doctor.id and s.user_id != user.id) else "patient",
                }
                # Get counterpart name
                if s.doctor_id and s.doctor_id != (doctor.id if doctor else None):
                    doc = await session.get(Doctor, s.doctor_id)
                    entry["doctor_name"] = doc.full_name if doc else "Unknown"
                elif s.doctor_id and doctor and s.doctor_id == doctor.id:
                    patient = await session.get(User, s.user_id)
                    entry["patient_telegram_id"] = patient.telegram_id if patient else None
                result.append(entry)
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to fetch sessions for %d", telegram_id)
        raise HTTPException(status_code=500, detail="Internal server error")

    return result


# ── GET /api/search/questions — Search Q&A ───────────────────────────────

@app.get("/api/search/questions")
async def search_questions(q: str = "", limit: int = 20):
    """Search approved/answered questions by text."""
    from bot.database import session_factory
    from bot.models.question import Question, QuestionStatus
    from sqlalchemy import select, func

    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    term = q.strip().lower()

    try:
        async with session_factory() as session:
            questions = (await session.execute(
                select(Question).where(
                    Question.status.in_([QuestionStatus.APPROVED, QuestionStatus.ANSWERED]),
                    (func.lower(Question.text).contains(term))
                    | (func.lower(Question.answer_text).contains(term))
                ).order_by(Question.created_at.desc()).limit(limit)
            )).scalars().all()
    except Exception:
        logger.exception("Failed to search questions")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": q.id,
            "category": q.category.value if hasattr(q.category, "value") else q.category,
            "text": q.text,
            "is_anonymous": q.is_anonymous,
            "status": q.status.value,
            "answer_text": q.answer_text,
            "created_at": str(q.created_at),
            "answered_at": str(q.answered_at) if q.answered_at else None,
        }
        for q in questions
    ]


# ── GET /api/search/doctors — Search doctors ─────────────────────────────

@app.get("/api/search/doctors")
async def search_doctors(q: str = ""):
    """Search verified doctors by name or specialty."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor, Specialty
    from sqlalchemy import select, func

    if not q.strip():
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required")

    term = q.strip().lower()

    try:
        # Try matching as specialty enum value
        specialty_match = None
        for sp in Specialty:
            if term in sp.value.lower() or sp.value.lower() in term:
                specialty_match = sp
                break

        async with session_factory() as session:
            conditions = [func.lower(Doctor.full_name).contains(term)]
            if specialty_match:
                conditions.append(Doctor.specialty == specialty_match)

            from sqlalchemy import or_
            doctors = (await session.execute(
                select(Doctor).where(
                    Doctor.is_verified.is_(True),
                    or_(*conditions),
                )
            )).scalars().all()
    except Exception:
        logger.exception("Failed to search doctors")
        raise HTTPException(status_code=500, detail="Internal server error")

    return [
        {
            "id": d.id,
            "full_name": d.full_name,
            "specialty": d.specialty.value if hasattr(d.specialty, "value") else d.specialty,
            "specialties": d.specialties or [d.specialty.value if hasattr(d.specialty, "value") else d.specialty],
            "bio": d.bio,
            "is_available": d.is_available,
            "rating_avg": round(d.rating_avg, 2),
            "rating_count": d.rating_count,
            "languages": d.languages,
            "profile_photo_url": d.profile_photo_file_id,
        }
        for d in doctors
    ]


# ── POST /api/admin/doctors/register — Admin registers a doctor (auto-verified) ──

@app.post("/api/admin/doctors/register")
async def admin_register_doctor(request: Request):
    """Admin registers a doctor directly — auto-verified, no approval needed."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor, Specialty, RegistrationStatus
    from bot.models.user import User
    from sqlalchemy import select
    from datetime import datetime, timezone

    body = await request.json()
    admin_telegram_id = body.get("admin_telegram_id")

    # Verify caller is admin
    if admin_telegram_id not in settings.admin_ids:
        raise HTTPException(status_code=403, detail="Not authorized")

    full_name = body.get("full_name")
    license_number = body.get("license_number")
    specialty = body.get("specialty")
    specialties = body.get("specialties", [])
    languages = body.get("languages", ["en"])
    bio = body.get("bio", "")
    telegram_username = body.get("telegram_username")
    phone = body.get("phone")
    sex = body.get("sex")
    sub_specialization = body.get("sub_specialization")
    profile_photo_url = body.get("profile_photo_url")
    license_document_url = body.get("license_document_url")

    if not full_name or not license_number or not specialty:
        raise HTTPException(status_code=400, detail="full_name, license_number, and specialty are required")

    try:
        spec_enum = Specialty(specialty)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid specialty: {specialty}")

    from bot.models.doctor import Sex
    sex_enum = None
    if sex:
        try:
            sex_enum = Sex(sex)
        except ValueError:
            pass

    try:
        async with session_factory() as session:
            # Check license uniqueness
            existing = (await session.execute(
                select(Doctor).where(Doctor.license_number == license_number)
            )).scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=409, detail="License number already registered")

            # Always generate signup token — doctor links TG account via deep link
            signup_token = uuid.uuid4().hex[:16]

            # Build specialties list: include primary + any additional
            all_specialties = specialties if isinstance(specialties, list) and specialties else [specialty]
            if specialty not in all_specialties:
                all_specialties.insert(0, specialty)

            doctor = Doctor(
                telegram_id=None,
                full_name=full_name,
                license_number=license_number,
                specialty=spec_enum,
                specialties=all_specialties,
                languages=languages if isinstance(languages, list) else [languages],
                bio=bio,
                sex=sex_enum,
                sub_specialization=sub_specialization,
                profile_photo_file_id=profile_photo_url,
                license_document_file_id=license_document_url,
                signup_token=signup_token,
                is_verified=True,
                is_available=True,
                registration_status=RegistrationStatus.APPROVED,
                applied_at=datetime.now(timezone.utc),
            )
            session.add(doctor)
            await session.commit()
            await session.refresh(doctor)
            doc_id = doctor.id
    except HTTPException:
        raise
    except Exception:
        logger.exception("Admin doctor registration failed")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Build signup link for the doctor to connect their Telegram
    signup_link = f"https://t.me/longimed_bot?start=signup_{signup_token}"

    return {
        "id": doc_id,
        "status": "approved",
        "is_verified": True,
        "signup_link": signup_link,
    }


# ── POST /api/doctors/register — Doctor self-registration ────────────────

@app.post("/api/doctors/register")
async def register_doctor(request: Request):
    """Doctor self-registration from Mini App."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor, Specialty, RegistrationStatus
    from sqlalchemy import select
    from datetime import datetime, timezone

    body = await request.json()
    telegram_id = body.get("telegram_id")
    full_name = body.get("full_name")
    license_number = body.get("license_number")
    specialty = body.get("specialty")
    languages = body.get("languages", ["en"])
    bio = body.get("bio")

    if not telegram_id or not full_name or not license_number or not specialty:
        raise HTTPException(
            status_code=400,
            detail="telegram_id, full_name, license_number, and specialty are required",
        )

    try:
        spec_enum = Specialty(specialty)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid specialty: {specialty}")

    try:
        async with session_factory() as session:
            # Check license uniqueness
            existing = (await session.execute(
                select(Doctor).where(Doctor.license_number == license_number)
            )).scalar_one_or_none()
            if existing:
                raise HTTPException(status_code=409, detail="License number already registered")

            # Check telegram_id uniqueness
            existing_tg = (await session.execute(
                select(Doctor).where(Doctor.telegram_id == telegram_id)
            )).scalar_one_or_none()
            if existing_tg:
                raise HTTPException(status_code=409, detail="Telegram account already registered as doctor")

            doctor = Doctor(
                telegram_id=telegram_id,
                full_name=full_name,
                license_number=license_number,
                specialty=spec_enum,
                languages=languages if isinstance(languages, list) else [languages],
                bio=bio,
                is_verified=False,
                registration_status=RegistrationStatus.PENDING,
                applied_at=datetime.now(timezone.utc),
            )
            session.add(doctor)
            await session.commit()
            await session.refresh(doctor)
            doc_id = doctor.id
    except HTTPException:
        raise
    except Exception:
        logger.exception("Failed to register doctor")
        raise HTTPException(status_code=500, detail="Internal server error")

    # Notify admins
    for admin_id in settings.admin_ids:
        await _tg_notify(
            admin_id,
            f"New doctor registration pending approval:\n"
            f"Name: {full_name}\nLicense: {license_number}\nSpecialty: {specialty}",
        )

    return {"id": doc_id, "status": "pending"}


# ── Doctor Waitlist — patients waiting for a doctor ──────────────────────

@app.get("/api/doctors/waitlist/{telegram_id}")
async def doctor_waitlist(telegram_id: int):
    """Get the patient waiting list for a doctor (or all if general)."""
    from bot.database import session_factory
    from bot.models.doctor import Doctor
    from bot.models.waitlist import Waitlist, WaitlistStatus
    from bot.models.user import User
    from bot.models.session import Session as CS, SessionStatus
    from sqlalchemy import select, or_

    async with session_factory() as session:
        # Verify doctor
        doc_result = await session.execute(
            select(Doctor).where(Doctor.telegram_id == telegram_id)
        )
        doctor = doc_result.scalar_one_or_none()
        if not doctor:
            raise HTTPException(status_code=404, detail="Doctor not found")

        # Get waitlist entries for this doctor or their specialty
        wl_result = await session.execute(
            select(Waitlist, User).join(User, Waitlist.user_id == User.id).where(
                Waitlist.status == WaitlistStatus.WAITING,
                or_(
                    Waitlist.doctor_id == doctor.id,
                    Waitlist.specialty == doctor.specialty.value,
                ),
            ).order_by(Waitlist.position.asc())
        )
        waitlist_rows = wl_result.all()

        # Also get pending/awaiting sessions assigned to this doctor
        session_result = await session.execute(
            select(CS, User).join(User, CS.user_id == User.id).where(
                CS.doctor_id == doctor.id,
                CS.status.in_([SessionStatus.AWAITING_DOCTOR, SessionStatus.PENDING_APPROVAL]),
            ).order_by(CS.created_at.asc())
        )
        pending_sessions = session_result.all()

    items = []

    for wl, user in waitlist_rows:
        items.append({
            "type": "waitlist",
            "id": wl.id,
            "position": wl.position,
            "patient_name": f"Patient #{user.id}",
            "patient_phone": user.phone,
            "specialty": wl.specialty,
            "created_at": str(wl.created_at) if hasattr(wl, 'created_at') else "",
        })

    for sess, user in pending_sessions:
        items.append({
            "type": "pending_session",
            "id": sess.id,
            "status": sess.status.value,
            "patient_name": f"Patient #{user.id}",
            "patient_phone": user.phone,
            "issue": sess.issue_description[:100] if sess.issue_description else "",
            "package": sess.package.value,
            "created_at": str(sess.created_at),
        })

    return {"doctor_id": doctor.id, "doctor_name": doctor.full_name, "waiting": items}


# ── Phase II webhooks (stubs) ──────────────────────────────────────────────

@app.post("/webhooks/chapa")
async def chapa_webhook():
    return {"status": "not_implemented"}


@app.post("/webhooks/stripe")
async def stripe_webhook():
    return {"status": "not_implemented"}
