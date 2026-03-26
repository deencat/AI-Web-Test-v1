"""
Workflow file upload endpoint.

POST /api/v1/uploads/workflow-files

Accepts a single file that browser-use will inject via setInputFiles().
The returned server_path is passed as available_file_paths in the
GenerateTestsRequest payload.

Security:
- JWT authentication required
- Allowed extensions: images + PDF + common documents
- Max size: 50 MB
- Filename is sanitised (basename only) and stored under a UUID sub-directory
  to prevent path traversal and collisions.
"""

import os
import uuid
from pathlib import Path, PurePosixPath

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from pydantic import BaseModel

from app.api import deps
from app.models.user import User

router = APIRouter()

# ---------------------------------------------------------------------------
# Configuration — can be patched in tests
# ---------------------------------------------------------------------------

UPLOAD_DIR = "uploads/workflow-files"

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

ALLOWED_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp",  # images (eKYC photos)
    ".pdf",                                     # documents
    ".doc", ".docx",                            # Word documents
    ".csv", ".txt",                             # data files
}


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------

class WorkflowFileUploadResponse(BaseModel):
    server_path: str
    filename: str
    size: int


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/uploads/workflow-files",
    response_model=WorkflowFileUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload a local file for use in a workflow",
    description=(
        "Saves a file to the server and returns the server-side path that can be "
        "passed as `available_file_paths` in the generate-tests request. "
        "browser-use then calls `setInputFiles(server_path)` during the workflow."
    ),
)
async def upload_workflow_file(
    file: UploadFile = File(...),
    current_user: User = Depends(deps.get_current_active_user),
):
    """Upload a file to be used by the browser-use agent (e.g. eKYC image)."""

    # --- Sanitise filename to prevent path traversal ---
    raw_name = file.filename or "upload"
    safe_name = Path(raw_name).name  # strips any directory components

    # --- Validate extension ---
    ext = Path(safe_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type '{ext}' is not allowed. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # --- Read content (enforce size limit before writing to disk) ---
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
        )

    # --- Build unique destination path ---
    upload_root = Path(UPLOAD_DIR)
    dest_dir = upload_root / str(uuid.uuid4())
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / safe_name

    # Final safety check: ensure resolved path is still inside upload_root
    try:
        dest_path.resolve().relative_to(upload_root.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename.",
        )

    # --- Write file ---
    dest_path.write_bytes(content)

    return WorkflowFileUploadResponse(
        server_path=str(dest_path),
        filename=safe_name,
        size=len(content),
    )
