import os
import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import ValidationError
from sqlmodel import Session

from app.core.db import get_session
from app.dependencies import SessionDep, require_admin
from app.models import User
from app.schemas.destination_schema import DestinationCreate, DestinationRead, DestinationUpdate
from app.schemas.optimization_schema import BudgetEstimateResult
from app.services.budget_optimizer import BudgetOptimizer
from app.services.destination_service import DestinationService
from app.services.activity_log_service import ActivityLogService


router = APIRouter(prefix="/destinations", tags=["destinations"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

class DestinationRouter:

    @router.get("/", status_code=200)
    def get_destinations(
        session: Session = Depends(get_session),
        offset: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100),
        category: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        description: Optional[str] = Query(None),
        rating_min: Optional[int] = Query(None, ge=1, le=5),
        permit_required: Optional[bool] = Query(None),
        province: Optional[str] = Query(None),
        district: Optional[str] = Query(None),
        place: Optional[str] = Query(None),
    ):
        return DestinationService(session).get_destinations(
            offset=offset,
            limit=limit,
            category=category,
            name=name,
            description=description,
            rating_min=rating_min,
            permit_required=permit_required,
            province=province,
            district=district,
            place=place,
        )
    

    @router.get("/stats", status_code=200)
    def get_destinations_stats(session: Session = Depends(get_session)):
        return DestinationService(session).get_destinations_stats()

    @router.get("/{destination_id}")
    async def get_destination_by_id(session: SessionDep, destination_id: uuid.UUID):
        return DestinationService(session).get_destination_by_id(str(destination_id))

    @router.get("/{destination_id}/budget-estimate")
    def get_destination_budget_estimate(
        session: SessionDep,
        destination_id: uuid.UUID,
        days: int = Query(7, ge=1, le=60),
        fee_category: str = Query("Foreign"),
    ) -> BudgetEstimateResult:
        """Per-destination average budget guide used to pre-fill the budget planner.

        Standard-tier food + accommodation (one person) plus one-time
        permits/entry fees, so the suggested budget varies by destination.
        """
        return BudgetOptimizer(session).estimate(
            str(destination_id), days=days, fee_category=fee_category
        )

    @router.post("/", status_code=201)
    async def create_destination(
        session: SessionDep,
        admin: Annotated[User, Depends(require_admin)],
        destination: str = Form(...),
        featured_file: Optional[UploadFile] = File(default=None),
        files: Optional[List[UploadFile]] = File(default=None),
    ):
        """Create a new destination with a featured cover photo (and optional gallery)."""
        if not files and not featured_file:
            raise HTTPException(status_code=422, detail="A featured or gallery photo is required")

        photo_uploads = []
        for file in files or []:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                )
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max {MAX_FILE_SIZE // (1024 * 1024)} MB",
                )
            photo_uploads.append((file.filename or "photo.jpg", content))

        featured = None
        if featured_file:
            ext = os.path.splitext(featured_file.filename or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                )
            content = await featured_file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max {MAX_FILE_SIZE // (1024 * 1024)} MB",
                )
            featured = (featured_file.filename or "featured.jpg", content)

        try:
            destination_data = DestinationCreate.model_validate_json(destination)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors(include_url=False, include_context=False)) from exc
        result = DestinationService(session).create_destination(
            destination_data, photo_uploads=photo_uploads, uploaded_by=admin.id, featured_file=featured
        )
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Created", target=f"Destination: {destination_data.name}", type="content",
        )
        return result
    
    @router.put("/{destination_id}")
    async def update_destination(
        session: SessionDep,
        destination_id: uuid.UUID,
        admin: Annotated[User, Depends(require_admin)],
        destination: str = Form(...),
        featured_file: Optional[UploadFile] = File(default=None),
        files: Optional[List[UploadFile]] = File(default=None),
    ):
        """Update a destination by ID (multipart: destination JSON + optional photos)."""
        photo_uploads = []
        for file in files or []:
            ext = os.path.splitext(file.filename or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                )
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max {MAX_FILE_SIZE // (1024 * 1024)} MB",
                )
            photo_uploads.append((file.filename or "photo.jpg", content))

        featured = None
        if featured_file:
            ext = os.path.splitext(featured_file.filename or "")[1].lower()
            if ext not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
                )
            content = await featured_file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Max {MAX_FILE_SIZE // (1024 * 1024)} MB",
                )
            featured = (featured_file.filename or "featured.jpg", content)

        try:
            destination_data = DestinationUpdate.model_validate_json(destination)
        except ValidationError as exc:
            raise HTTPException(status_code=422, detail=exc.errors(include_url=False, include_context=False)) from exc

        result = DestinationService(session).update_destination(
            str(destination_id), destination_data,
            photo_uploads=photo_uploads, uploaded_by=admin.id, featured_file=featured,
        )
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Updated", target=f"Destination: {result['destination']['name']}", type="content",
        )
        return result
    
    @router.delete("/{destination_id}")
    async def delete_destination(session: SessionDep, destination_id: uuid.UUID, admin: Annotated[User, Depends(require_admin)]):
        """Delete a destination by ID."""
        result = DestinationService(session).get_destination_by_id(str(destination_id))
        name = result["destination"]["name"]
        result = DestinationService(session).delete_destination(str(destination_id))
        ActivityLogService(session).log(
            user_id=admin.id, user_name=admin.name,
            action="Deleted", target=f"Destination: {name}", type="content",
        )
        return result