from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from soccer_analytics.api.jobs import create_job, get_job, run_pipeline_sync
from soccer_analytics.api.schemas import (
    AnalyticsResponse,
    JobCreatedResponse,
    JobStatusResponse,
    PossessionData,
)

router = APIRouter(prefix="/api")

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")


@router.post("/upload", response_model=JobCreatedResponse)
async def upload_video(file: UploadFile) -> JobCreatedResponse:
    UPLOAD_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    filename = file.filename or "video.mp4"
    job = create_job(input_filename=filename, input_path="", output_path="")

    input_path = UPLOAD_DIR / f"{job.id}_{filename}"
    output_path = OUTPUT_DIR / f"{job.id}_output.mp4"

    content = await file.read()
    input_path.write_bytes(content)

    job.input_path = str(input_path.resolve())
    job.output_path = str(output_path.resolve())

    asyncio.get_event_loop().run_in_executor(None, run_pipeline_sync, job)

    return JobCreatedResponse(job_id=job.id, status=job.status)


@router.get("/jobs/{job_id}/status", response_model=JobStatusResponse)
async def job_status(job_id: str) -> JobStatusResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        phase=job.phase,
        current_frame=job.current_frame,
        total_frames=job.total_frames,
        progress_pct=job.progress_pct,
        error=job.error,
    )


@router.get("/jobs/{job_id}/analytics", response_model=AnalyticsResponse)
async def job_analytics(job_id: str) -> AnalyticsResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    if job.analytics is None:
        raise HTTPException(status_code=400, detail="No analytics available")

    possession = job.analytics.get("possession", {})
    return AnalyticsResponse(
        possession=PossessionData(
            team_0=possession.get("team_0", 0.0),
            team_1=possession.get("team_1", 0.0),
        ),
        player_stats=job.analytics.get("player_stats", []),
        events=job.analytics.get("events", []),
    )


@router.get("/jobs/{job_id}/video")
async def job_video(job_id: str) -> FileResponse:
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")

    output = Path(job.output_path)
    if not output.exists():
        raise HTTPException(status_code=404, detail="Output video not found")

    return FileResponse(path=str(output), media_type="video/mp4", filename=f"{job_id}_output.mp4")
